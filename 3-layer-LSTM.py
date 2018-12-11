import os
import sys
import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt 

import keras
from keras.models import Sequential, Model
from keras import metrics
from keras.callbacks import EarlyStopping, Callback, ModelCheckpoint, TensorBoard
from keras import backend as K
from keras.layers import LSTM, InputLayer, Dense, Input, Flatten, concatenate, Reshape, Dropout, Activation, SimpleRNN, \
    GRU, Embedding, Lambda, TimeDistributed
from keras.optimizers import Adam, RMSprop


path = os.getcwd() + '/malware_API_dataset_filtered_paper_500.csv'
# path = os.getcwd() + '/filtered_sample.txt'
ori_data = open(path)
data = []
dataY = []
#encoding id for all labels and APIs
idmap = {'' : 0}
idmapy = {}
# encode with labels, the unsure label is encoded as 1
cnt_y = 0
cnt = 1
#max length of all the data lines
ma_len = 0
for eachline in ori_data:
	t = eachline.strip().split(',')
	label_real = t[0]
	if label_real not in idmapy:
		idmapy[label_real] = cnt_y
		cnt_y += 1
	dataY.append(idmapy[label_real])

	t = t[1 : ]
	for i in range(len(t)):
		if t[i] not in idmap:
			idmap[t[i]] = cnt
			cnt += 1
		t[i] = idmap[t[i]]
	ma_len = max(ma_len, len(t))
	data.append(t)


datanewX = np.array(data)
datanewY = np.array(dataY)


def shuffle(X, y):
	ii = np.arange(X.shape[0])
	ii = np.random.shuffle(ii)
	X_rand = X[ii]
	y_rand = y[ii]
	X_new = np.reshape(X_rand.shape[1:])
	y_new = np.reshape(y_rand.shape[1:])
	return (X_new, y_new)

# take the 80% of data as train_set, 20% to test
train_len=int(0.8*datanewX.shape[0])
traindataX=datanewX[:train_len,:]
testdataX=datanewX[train_len:,:]
traindataY=datanewY[:train_len]
testdataY=datanewY[train_len:]

max_epoch = 50
batch_size = 500
max_seq_len = ma_len

log_path = './log_3layer_lstm_lr=0.001/'
model_name = log_path + './3_layer_lstm.h5'

inputx = Input(shape=(max_seq_len,), name= 'user_input')
#input_dim is the number of vocubularies (total APIs), input_length is the number of words (APIs) token into consideration in the context.
inputemb = Embedding(output_dim = 50, input_dim = len(idmap)+1, mask_zero = True, input_length = max_seq_len)(inputx)
lstmout1 = (LSTM(units=128, return_sequences=True, dropout=0.5, recurrent_dropout=0.5))(inputemb)
lstmout2 = (LSTM(units=128, return_sequences=True, dropout=0.5, recurrent_dropout=0.5))(lstmout1)
lstmout3 = (LSTM(units=128, return_sequences=False, dropout=0.5, recurrent_dropout=0.5))(lstmout2)
out = Dense(len(idmapy), activation='softmax', name='out')(lstmout3)


model = Model(inputs = inputx, outputs = out)
sgd = Adam(lr = 0.001, beta_1 = 0.9, beta_2 = 0.999, epsilon = 1e-8, decay = 1e-6)
model.compile(loss = 'sparse_categorical_crossentropy', optimizer = sgd, metrics = ['sparse_categorical_accuracy'])
# earlyStopping = EarlyStopping(monitor = 'val_loss', patience = 5, verbose = 0, mode = 'min')

class AccuracyHistory(keras.callbacks.Callback):
	def on_train_begin(self,logs={}):
		self.acc = []
	def on_epoch_end(self,batch, logs ={}):
		self.acc.append(logs.get('acc'))

history = AccuracyHistory()
tbCallBack = TensorBoard(log_dir = log_path, histogram_freq =0, write_graph = True, write_images = True)
checkpointer = ModelCheckpoint(filepath=log_path +'weights.hdf5', verbose=1, save_best_only=True,period=10)
model.fit(traindataX, traindataY, batch_size = batch_size, epochs = max_epoch, verbose = 1, validation_split = 0.1, callbacks = [history,tbCallBack,checkpointer])

model.save(model_name)

score = model.evaluate(testdataX, testdataY, batch_size = batch_size, verbose =0)

print (score)

# fig= plt.figure()
# plt.plot(history.acc)
# plt.xlabel('epochs')
# plt.ylabel('Accuracy')
# plt.show()


		  

