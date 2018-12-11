import os
import pandas

import numpy as np
from keras.callbacks import TensorBoard

from keras.layers import  merge, Convolution2D, MaxPooling2D, Dropout
from keras.layers.core import Reshape, Flatten
from keras.models import Model,load_model
# from keras import metrics
from keras.callbacks import EarlyStopping,ModelCheckpoint
from keras.layers import  Dense, Input, Embedding
from keras.optimizers import Adam #, RMSprop

## extra imports to set GPU options
import tensorflow as tf
from keras import backend as k

np.random.seed(2048)

###################################
# TensorFlow wizardry
config = tf.ConfigProto()

# Don't pre-allocate memory; allocate as-needed
config.gpu_options.allow_growth = True

# Only allow a total of half the GPU memory to be allocated
config.gpu_options.per_process_gpu_memory_fraction = 0.3

# Create a session with the above options specified.
k.tensorflow_backend.set_session(tf.Session(config=config))
###################################

def pro_processing(data_path, pre_processed_data_path, label_path):
    ori_data = open(data_path)
    data = []
    dataY = []
    # encoding id for all labels and APIs
    idmap = {'': 0}
    idmapy = {}
    # encode with labels, the unsure label is encoded as 1
    cnt_y = 0
    cnt = 1
    # max length of all the data lines
    ma_len = 0
    for eachline in ori_data:
        t = eachline.strip().split(',')
        label_real = t[0]
        if label_real.split('.')[0] == 'Trojan-Ransom':
            idmapy[label_real] = 1
        else:
            idmapy[label_real] = 0
        dataY.append(idmapy[label_real])

        t = t[1:]
        for i in range(len(t)):
            if t[i] not in idmap:
                idmap[t[i]] = cnt
                cnt += 1
            t[i] = idmap[t[i]]
        ma_len = max(ma_len, len(t))
        data.append(t)

    datanewX = np.array(data)
    datanewY = np.array(dataY)

    np.savetxt(pre_processed_data_path, datanewX, delimiter=",", fmt='%d')
    np.savetxt(label_path, datanewY, delimiter=",", fmt="%d")


def training(datanewX, datanewY,is_continue_training):

    print("building network....")
    ma_len = datanewX.shape[1]
    unique_opera = np.unique(datanewX,return_counts=False)
    input_dim = len(unique_opera)
    output_dim = np.amax(datanewY).astype("int64") + 1

    # take the 80% of data as train_set, 20% to test
    train_len = int(0.8 * datanewX.shape[0])

    # train_len1 = int(0.3 * datanewX.shape[0
    traindataX = datanewX[:train_len, :]
    test_len = int(0.2 * datanewX.shape[0])
    testdataX = datanewX[train_len: :]
    traindataY = datanewY[:train_len]
    testdataY = datanewY[train_len: ]


    embedding_dim = 100
    filter_sizes = [3, 3, 3]
    num_filters = 128
    drop = 0.5


    Learning_rate = 0.001
    max_epoch = 50
    batch_size = 500
    max_seq_len = ma_len

    log_path = './log_1layer_CNN=0.001/'
    model_name = log_path + 'cnn.h5'

    if is_continue_training:
        load_path = log_path
        model =load_model(load_path + model_name)
        sgd = Adam(lr=Learning_rate/2, beta_1=0.9, beta_2=0.999, epsilon=1e-8, decay=1e-6)
        model.compile(loss='sparse_categorical_crossentropy', optimizer=sgd, metrics=['sparse_categorical_accuracy'])
        save_path = log_path + "continued"

    else:
        save_path = log_path
        inputs = Input(shape=(max_seq_len,), dtype='int32')
        embedding = Embedding(output_dim=embedding_dim, input_dim=input_dim, input_length=max_seq_len)(inputs)
        reshape = Reshape((max_seq_len, embedding_dim, 1))(embedding)

        conv_0 = Convolution2D(num_filters, filter_sizes[0], embedding_dim, border_mode='valid', init='normal',
                               activation='relu', dim_ordering='tf')(reshape)

        maxpool_0 = MaxPooling2D(pool_size=(max_seq_len - filter_sizes[0] + 1, 1), strides=(1, 1),
                                 border_mode='valid', dim_ordering='tf')(conv_0)

        flatten = Flatten()(maxpool_0)
        dropout = Dropout(drop)(flatten)

        dense1 = Dense(output_dim=1000, activation='relu')(dropout)
        dense2 = Dense(output_dim=1000, activation='relu')(dense1)
        output = Dense(output_dim=output_dim, activation='softmax')(dense2)

        model = Model(inputs=inputs, outputs=output)
        adam = Adam(lr=Learning_rate, beta_1=0.9, beta_2=0.999, epsilon=1e-8, decay=1e-6)
        model.compile(loss='sparse_categorical_crossentropy', optimizer=adam, metrics=['sparse_categorical_accuracy'])
        y_predicted = model.predict_classes(testdataX)
        print(y_predicted)

    #additional setting
    earlyStopping = EarlyStopping(monitor='sparse_categorical_accuracy', patience=10, verbose=0, mode='max')
    checkpointer = ModelCheckpoint(filepath=log_path +'weights.hdf5', verbose=1, save_best_only=True,period=10)
    tensorboard = TensorBoard(log_dir=save_path, histogram_freq=0, write_graph=True, write_images=False)

    print("training start....")
    history_callback = model.fit(traindataX, traindataY, batch_size=batch_size, epochs=max_epoch, verbose=1, validation_split=0.1,shuffle=True,callbacks=[earlyStopping, checkpointer, tensorboard])

    model.save(model_name)
    score = model.evaluate(testdataX, testdataY, batch_size=batch_size, verbose=0)

    print(score)


def main():
    # data_path = os.getcwd() + '/filtered_sample.csv'
    data_path = os.getcwd() + '/Ransomware_shuffled.csv'
    pre_processed_data = './pre_data.csv'
    label_path = './labels_ransom.csv'
    is_preProcessed = False
    is_continue_training = False

    datanewX=[]
    datanewY=[]

    while(not is_preProcessed):
        if os.path.isfile(pre_processed_data) and os.path.isfile(label_path):
            datanewX = np.genfromtxt(pre_processed_data, delimiter=',') #, dtype="float32"
            datanewY = np.genfromtxt(label_path,delimiter=',')
            is_preProcessed = True
            training(datanewX, datanewY, is_continue_training)
        else:
            pro_processing(data_path, pre_processed_data, label_path)       


main()

