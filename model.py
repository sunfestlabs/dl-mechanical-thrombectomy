#hyperparameters
import numpy as np
import tensorflow as tf
from preprocess import append_csv_features, get_mips_data, TICI_MAP
from tici_model import TICI_Model
from num_passes_model import Passes_Model
from matplotlib import pyplot as plt

def train(model, train_inputs, train_labels, predict_tici=False):
    nrows = train_labels.shape[0]
    nbatches = int(np.ceil(nrows/model.batch_size))
    accuracy = np.zeros(nbatches)
    total_under = np.zeros(nbatches)
    total_over = np.zeros(nbatches)
    if predict_tici:
        train_labels = np.array([row[1] for row in train_labels])
    else:
        train_labels = np.array([row[0] for row in train_labels])

    for batch in range(0,nbatches):
        # For every batch, compute then descend the gradients for the model's weights
        start_idx = batch * model.batch_size
        inputs = train_inputs[start_idx:min((start_idx + model.batch_size), nrows)]
        labels = train_labels[start_idx:min((start_idx + model.batch_size), nrows)]
        with tf.GradientTape() as tape:
            probabilities = model.call(inputs)
            loss = model.loss(probabilities, labels)
            acc, under, over, residuals = model.accuracy(probabilities, labels)
            accuracy[batch] = acc
            total_under[batch] = under
            total_over[batch] = over
            # model.loss_list.append(loss.numpy())
        gradients = tape.gradient(loss, model.trainable_variables)
        model.optimizer.apply_gradients(zip(gradients, model.trainable_variables))

    if predict_tici:
        print("Done! Train TICI accuracy: " + str(tf.reduce_mean(accuracy).numpy()))
    else:
        print("Done! Train # Passes accuracy: " + str(tf.reduce_mean(accuracy).numpy()))

def test(model, test_inputs, test_labels, predict_tici=False):
    nrows = test_labels.shape[0]
    nbatches = int(np.ceil(nrows / model.batch_size))
    accuracy = np.zeros(nbatches)
    total_under = np.zeros(nbatches)
    total_over = np.zeros(nbatches)

    if predict_tici:
        test_labels = np.array([row[1] for row in test_labels])
        total_residuals = np.zeros((nbatches, 7))
    else:
        test_labels = np.array([row[0] for row in test_labels])
        total_residuals = np.zeros((nbatches, 10))

    for batch in range(0, nbatches):
        start_idx = batch * model.batch_size
        inputs = test_inputs[start_idx:min((start_idx + model.batch_size), nrows)]
        labels = test_labels[start_idx:min((start_idx + model.batch_size), nrows)]
        probs = model.call(inputs)
        acc, under, over, residuals = model.accuracy(probs, labels)
        accuracy[batch] = acc
        total_under[batch] = under
        total_over[batch] = over
        total_residuals[batch] = residuals

    return tf.reduce_mean(accuracy), tf.reduce_mean(total_under), tf.reduce_mean(total_over), tf.reduce_mean(total_residuals, axis=0)


def main():
    num_tici_scores = len(TICI_MAP)
    max_passes = 10 # last class represents >=10 passes
    num_epochs = 10 # epochs that i've found good are 4, 5, 6, 8 -Chris

    train_data, train_labels, test_data, test_labels, vocab_size = append_csv_features(get_mips_data())

    tici_model = TICI_Model(vocab_size, num_tici_scores)
    passes_model = Passes_Model(vocab_size, max_passes)

    for i in range(num_epochs):
        print(i)
        indices = np.arange(train_data.shape[0])
        np.random.shuffle(indices)
        train_data = train_data[indices]
        train_labels = train_labels[indices]
        train(tici_model, train_data, train_labels, predict_tici=True)
        train(passes_model, train_data, train_labels)

    tici_acc, tici_over, tici_under, tici_residual = test(tici_model, test_data, test_labels, predict_tici=True)
    passes_acc, passes_over, passes_under, passes_residual = test(passes_model, test_data, test_labels)
    print("TICI Score Test Accuracy: " + str(tici_acc))
    print("TICI Overpredict Rate: " + str(tici_over))
    print("TICI Underpredict Rate: " + str(tici_under))
    print("TICI Residual: " + str(tici_residual))
    print("Num Passes Test Accuracy: " + str(passes_acc))
    print("Num Passes Overpredict Rate: " + str(passes_over))
    print("Num Passes Underpredict Rate: " + str(passes_under))
    print("Num Passes Residual : " + str(passes_residual))


if __name__ == '__main__':
    main()