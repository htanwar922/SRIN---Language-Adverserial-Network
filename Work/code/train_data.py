﻿#!/usr/bin/env ipython

#@title train_data.py

"""## Load data in the notebook
- ### Pre-trained embeddings in vocab
- ### Amazon reviews data in
> - train_src, dev_src, test_src
> - train_tgt, dev_tgt, test_tgt
"""

#import torch
#import torch.nn as nn
#import torch.nn.functional as functional
#import torch.optim as optim
#from torch.utils.data import DataLoader
#from torchnet.meter import ConfusionMeter

import tensorflow as tf
from tensorflow.keras import optimizers, losses
import json

import os, random, sys, logging, argparse
from tqdm import tqdm
from pathlib import Path
os.chdir(os.path.dirname(__file__))

from options import *
from data import *
from vocab import *
from utils import *

# output options
log.info('Training ADAN with options:')
log.info(opt)

def get_train_data(opt):
    #opt.n_vecs = 20000; opt.train_size_src = -1; opt.train_size_tgt = -1
    # vocab
    log.info(f'Loading Embeddings...')
    vocab = Vocab(opt.pre_trained_src_emb_file, opt.n_vecs)
    vocab.add_pre_trained_emb(opt.pre_trained_tgt_emb_file, opt.n_vecs)
    log.info(f'Done.')

    # datasets
    length = {}

    # src_lang datasets
    log.info(f'Loading src datasets...')
    reviews_src_obj = AmazonReviews(path=opt.data_path, max_seq_len=opt.max_seq_len)
    train_src = reviews_src_obj.load_data(lang=opt.src_lang, dat='train', lines=opt.train_size_src); length['train_src'] = len(train_src)
    dev_src = reviews_src_obj.load_data(lang=opt.src_lang, dat='dev', lines=-1); length['dev_src'] = len(dev_src)
    test_src = reviews_src_obj.load_data(lang=opt.src_lang, dat='test', lines=-1); length['test_src'] = len(test_src)
    log.info('Done loading src datasets.')

    # tgt_lang datasets
    log.info(f'Loading tgt datasets...')
    reviews_tgt_obj = AmazonReviews(path=opt.data_path, max_seq_len=opt.max_seq_len)
    train_tgt = reviews_tgt_obj.load_data(lang=opt.tgt_lang, dat='train', lines=opt.train_size_tgt); length['train_tgt'] = len(train_tgt)
    dev_tgt = reviews_tgt_obj.load_data(lang=opt.tgt_lang, dat='dev', lines=-1); length['dev_tgt'] = len(dev_tgt)
    test_tgt = reviews_tgt_obj.load_data(lang=opt.tgt_lang, dat='test', lines=-1); length['test_tgt'] = len(test_tgt)
    
    log.info('Done loading tgt datasets.')

    #opt.num_labels = max(reviews_src_obj.star_rating, reviews_tgt_obj.star_rating)
    if opt.max_seq_len < 0 or not opt.max_seq_len:
        maxlen_src, maxlen_tgt = max(list(len(x) for x in train_src)), max(list(len(x) for x in train_tgt))
        opt.max_seq_len = max(maxlen_src, maxlen_tgt)
    del reviews_src_obj, reviews_tgt_obj

    # pad src datasets (-> Dataset)
    log.info('Padding src datasets...')
    train_src = vocab.pad_sequences(train_src, max_len=opt.max_seq_len)
    dev_src = vocab.pad_sequences(dev_src, max_len=opt.max_seq_len)
    test_src = vocab.pad_sequences(test_src, max_len=opt.max_seq_len)
    log.info('Done padding src datasets...')

    # pad tgt datasets (-> Dataset)
    log.info('Padding tgt datasets...')
    train_tgt = vocab.pad_sequences(train_tgt, max_len=opt.max_seq_len)
    dev_tgt = vocab.pad_sequences(dev_tgt, max_len=opt.max_seq_len)
    test_tgt = vocab.pad_sequences(test_tgt, max_len=opt.max_seq_len)
    log.info('Done padding tgt datasets...')

    # dataset loaders
    log.info('Shuffling and batching...')
    train_src = train_src.shuffle(buffer_size=opt.buffer_size, reshuffle_each_iteration=True).batch(opt.batch_size).shuffle(length['train_src']//opt.batch_size).shuffle(length['train_src']//opt.batch_size).shuffle(length['train_src']//opt.batch_size)
    train_tgt = train_tgt.shuffle(buffer_size=opt.buffer_size, reshuffle_each_iteration=True).batch(opt.batch_size).shuffle(length['train_tgt']//opt.batch_size).shuffle(length['train_tgt']//opt.batch_size).shuffle(length['train_tgt']//opt.batch_size)
    with tf.device('CPU'):
        train_src_Q = tf.identity(train_src)
        train_tgt_Q = tf.identity(train_src)
    train_src_Q_iter = iter(train_src_Q)
    train_tgt_Q_iter = iter(train_tgt_Q)
    
    dev_src = dev_src.shuffle(buffer_size=opt.buffer_size, reshuffle_each_iteration=True).batch(opt.batch_size)
    dev_tgt = dev_tgt.shuffle(buffer_size=opt.buffer_size, reshuffle_each_iteration=True).batch(opt.batch_size)
    
    test_src = test_src.shuffle(buffer_size=opt.buffer_size, reshuffle_each_iteration=True).batch(opt.batch_size)
    test_tgt = test_tgt.shuffle(buffer_size=opt.buffer_size, reshuffle_each_iteration=True).batch(opt.batch_size)
    log.info('Done shuffling and batching.')

    return vocab, train_src, dev_src, test_src, train_tgt, dev_tgt, test_tgt, train_src_Q, train_tgt_Q, train_src_Q_iter, train_tgt_Q_iter, length

if __name__ == "__main__" and opt.notebook:
    # clear dumps
    tf.keras.backend.clear_session()
    tf.keras.backend.set_learning_phase(0)
    print(tf.keras.backend.learning_phase())
    vocab, train_src, dev_src, test_src, train_tgt, dev_tgt, test_tgt, train_src_Q, train_tgt_Q, train_src_Q_iter, train_tgt_Q_iter, length = get_train_data(opt)
