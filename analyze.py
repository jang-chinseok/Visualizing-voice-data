# visualisation tools for mimic2 
import matplotlib.pyplot as plt
from statistics import stdev, mode, mean, median
from statistics import StatisticsError
import argparse
import glob
import os
import csv
import copy
import seaborn as sns
import random
from text.cmudict import CMUDict

from jamo import h2j, j2hcj
from text import cleaners
from korean_romanizer.romanizer import Romanizer
import matplotlib.font_manager as fm
import "github.com/hangulize/hangulize"  #한글라이즈 를 사용해 보고 싶었으나 적용하지 못함.
'''from g2pk import G2p'''              #g2pk를 사용하고싶었지만, install과정에서 pip가 계속 고장나는 문제가 발생하여 포기.


fl = fm.FontProperties(fname="C:\WINDOWS\Fonts\malgun.ttf").get_name()  #한글자모의 경우, 폰트 그기가 맞지 않아 matplotlib에 정상표기되지 않는문제가 있는데, 
plt.rc('font',family=fl)                                                #이를 해결하기 위해 그 크기를 맞도록 보정해 주는 코드.
def get_audio_seconds(frames):
    return (frames*12.5)/1000


def append_data_statistics(meta_data):
    # get data statistics
    for char_cnt in meta_data:
        data = meta_data[char_cnt]["data"]
        audio_len_list = [d["audio_len"] for d in data]
        mean_audio_len = mean(audio_len_list)
        try:
            mode_audio_list = [round(d["audio_len"], 2) for d in data]
            mode_audio_len = mode(mode_audio_list)
        except StatisticsError:
            mode_audio_len = audio_len_list[0]
        median_audio_len = median(audio_len_list)

        try:
            std = stdev(
                d["audio_len"] for d in data
            )
        except:
            std = 0

        meta_data[char_cnt]["mean"] = mean_audio_len
        meta_data[char_cnt]["median"] = median_audio_len
        meta_data[char_cnt]["mode"] = mode_audio_len
        meta_data[char_cnt]["std"] = std
    return meta_data


def process_meta_data(path):
    meta_data = {}

    # load meta data
    with open(path, 'r',encoding='utf-8') as f:     
        data = csv.reader(f, delimiter='|')
        for row in data:
            frames = int(row[2])
            utt = row[3]
            audio_len = get_audio_seconds(frames)
            char_count = len(utt)
            if not meta_data.get(char_count):
                meta_data[char_count] = {
                    "data": []
                }

            meta_data[char_count]["data"].append(
                {
                    "utt": utt,
                    "frames": frames,
                    "audio_len": audio_len,
                    "row": "{}|{}|{}|{}".format(row[0], row[1], row[2], row[3])
                }
            )

    meta_data = append_data_statistics(meta_data)

    return meta_data


def get_data_points(meta_data):
    x = [char_cnt for char_cnt in meta_data]
    y_avg = [meta_data[d]['mean'] for d in meta_data]
    y_mode = [meta_data[d]['mode'] for d in meta_data]
    y_median = [meta_data[d]['median'] for d in meta_data]
    y_std = [meta_data[d]['std'] for d in meta_data]
    y_num_samples = [len(meta_data[d]['data']) for d in meta_data]
    return {
        "x": x,
        "y_avg": y_avg,
        "y_mode": y_mode,
        "y_median": y_median,
        "y_std": y_std,
        "y_num_samples": y_num_samples
    }


def save_training(file_path, meta_data):
    rows = []
    for char_cnt in meta_data:
        data = meta_data[char_cnt]['data']
        for d in data:
            rows.append(d['row'] + "\n")

    random.shuffle(rows)
    with open(file_path, 'w+') as f:
        for row in rows:
            f.write(row)


def plot(meta_data, save_path=None):
    save = False
    if save_path:
        save = True

    graph_data = get_data_points(meta_data)
    x = graph_data['x']
    y_avg = graph_data['y_avg']
    y_std = graph_data['y_std']
    y_mode = graph_data['y_mode']
    y_median = graph_data['y_median']
    y_num_samples = graph_data['y_num_samples']
   
    plt.figure()
    plt.plot(x, y_avg, 'ro')
    plt.xlabel("character lengths", fontsize=30)
    plt.ylabel("avg seconds", fontsize=30)
    if save:
        name = "char_len_vs_avg_secs"
        plt.savefig(os.path.join(save_path, name))
    
    plt.figure()
    plt.plot(x, y_mode, 'ro')
    plt.xlabel("character lengths", fontsize=30)
    plt.ylabel("mode seconds", fontsize=30)
    if save:
        name = "char_len_vs_mode_secs"
        plt.savefig(os.path.join(save_path, name))

    plt.figure()
    plt.plot(x, y_median, 'ro')
    plt.xlabel("character lengths", fontsize=30)
    plt.ylabel("median seconds", fontsize=30)
    if save:
        name = "char_len_vs_med_secs"
        plt.savefig(os.path.join(save_path, name))

    plt.figure()
    plt.plot(x, y_std, 'ro')
    plt.xlabel("character lengths", fontsize=30)
    plt.ylabel("standard deviation", fontsize=30)
    if save:
        name = "char_len_vs_std"
        plt.savefig(os.path.join(save_path, name))

    plt.figure()
    plt.plot(x, y_num_samples, 'ro')
    plt.xlabel("character lengths", fontsize=30)
    plt.ylabel("number of samples", fontsize=30)
    if save:
        name = "char_len_vs_num_samples"
        plt.savefig(os.path.join(save_path, name))
        
def convert_phonemes_Symbols(word):             #초성과 중성을 분류해 주기 위해서 만들어 준 함수-초성과 종성이 가지는 발음과 매칭시켜줌.
    if word == 'ㅂ':                             #자모 라이브러리를 사용할 경우, 초 중 종으로 나누어지게 되는데, 이어지는 코드에서 이를 리스트로 저장함.
        return 'p0'                             #이 코드는 거기에서 인덱스 기준으로 0,1에 한해서 적용하기 위한 함수임.
    elif word == 'ㅍ':
        return 'ph'
    elif word == 'ㅃ':
        return 'pp'
    elif word == 'ㄷ':
        return 't0'
    elif word == 'ㅌ':
        return 'th'
    elif word == 'ㄸ':
        return 'tt'
    elif word == 'ㄱ':
        return 'k0'
    elif word == 'ㅋ':
        return 'kh'
    elif word == 'ㄲ':
        return 'kk'
    elif word == 'ㅅ':
        return 's0'
    elif word == 'ㅆ':
        return 'ss'
    elif word == 'ㅎ':
        return 'h0'
    elif word == 'ㅈ':
        return 'c0'
    elif word == 'ㅊ':
        return 'ch'
    elif word == 'ㅉ':
        return 'cc'
    elif word == 'ㅁ':
        return 'mm'
    elif word == 'ㄴ':
        return 'nn'
    elif word == 'ㄹ':
        return 'rr'

    #여기부터는 모음
    elif word == 'ㅣ':
        return 'ii'
    elif word == 'ㅔ':
        return 'ee'
    elif word == 'ㅐ':
        return 'qq'
    elif word == 'ㅏ':
        return 'aa'
    elif word == 'ㅡ':
        return 'xx'
    elif word == 'ㅓ':  
        return 'vv'
    elif word == 'ㅜ':
        return 'uu'
    elif word == 'ㅗ':
        return 'oo'
    elif word == 'ㅖ':
        return 'ye'
    elif word == 'ㅒ':
        return 'yq'
    elif word == 'ㅑ':
        return 'ya'
    elif word == 'ㅕ':
        return 'yv'
    elif word == 'ㅠ':
        return 'yu'
    elif word == 'ㅛ':  
        return 'yo'
    elif word == 'ㅟ':
        return 'wi'
    elif word == 'ㅚ':
        return 'wo'
    elif word == 'ㅙ':
        return 'wq'
    elif word == 'ㅞ':
        return 'we'
    elif word == 'ㅘ':
        return 'wa'
    elif word == 'ㅝ':
        return 'wv'
    elif word == 'ㅢ':
        return 'xi'    
    
def convert_phonemes_Symbols_coda(word):        #위 함수에서 초성과 종성을 구별했기 때문에, 마지막 리스트 인덱스 2번은 종성이 됨, 이는 존재 할 시에만 적용.
        #이 아래로는 종성발음                    #종성의 발음을 
    if word == 'ㅂ':     
        return 'pf'
    elif word == 'ㅍ':
        return 'ph'
    elif word == 'ㄷ':
        return 'tf'
    elif word == 'ㅌ':
        return 'th'
    elif word == 'ㄱ':
        return 'kf'
    elif word == 'ㅋ':
        return 'kh'
    elif word == 'ㄲ':
        return 'kk'
    elif word == 'ㅅ':
        return 's0'
    elif word == 'ㅆ':  
        return 'ss'
    elif word == 'ㅎ':
        return 'h0'
    elif word == 'ㅈ':
        return 'c0'
    elif word == 'ㅊ':
        return 'ch'
    elif word == 'ㅁ':
        return 'mf'
    elif word == 'ㄴ':
        return 'nf'
    elif word == 'ㅇ':
        return 'ng'
    elif word == 'ㄹ':
        return 'll'
    elif word == 'ㄳ':  
        return 'ks'
    elif word == 'ㄵ':
        return 'nc'
    elif word == 'ㄶ':
        return 'nh'
    elif word == 'ㄺ':
        return 'lk'
    elif word == 'ㄻ':
        return 'lm'
    elif word == 'ㄼ':
        return 'lb'
    elif word == 'ㄽ':
        return 'ls'
    elif word == 'ㄾ':
        return 'lt'
    elif word == 'ㄿ':  
        return 'lp'
    elif word == 'ㅀ':
        return 'lh'
    elif word == 'ㅄ':
        return 'ps'

def plot_phonemes(train_path, cmu_dict_path, save_path):
    cmudict = CMUDict(cmu_dict_path)

    phonemes = {}

    with open(train_path, 'r', encoding='utf-8') as f:
        data = csv.reader(f, delimiter='|')
        phonemes["None"] = 0
        for row in data:
            words = row[3].split()  #데이터에서 3번째 인덱스가 문장이기 때문에, 이 데이터를 추출.
            
            for word in words:              #추출한 문자 데이터를. 공백을 기준으로 나누어 단어별로 분류 한 후 그 단어마다 작업을 진행.
                '''parse = G2p(word)'''     #G2p가 정상적으로 import 및 install되었을 경우 단어를 실제 발음으로 변화시기지 위한 코드.
                word=list(word)             #단어를 한개씩 작업하기 위해 리스트화 시키는 코드.
                
                for i in word :
                    pho = j2hcj(h2j(i))     #한글자씩 자모를 통해 초 중 종성으로 분해 한 후에 저장.
                    
                    if pho:
                        indie = list(pho)           

                        if  indie[0]!= '.'and indie[0] != '?' and indie[0] != '!' and indie[0] != ',':  #문장기호 제외.
                            indie[0]=convert_phonemes_Symbols(indie[0])                                 #위에서 쓴 초성과 중성에 대한 매칭을 위한 함수 호출.
                            indie[1]=convert_phonemes_Symbols(indie[1])
                            if len(indie)==3:
                                indie[2]=convert_phonemes_Symbols_coda(indie[2])                        #리스트의 길이가 3이라는 것은 종성이 존재. 이 경우에만 종성발음 변환.
                        for nemes in indie:
                            if phonemes.get(nemes):                                                     #변환된 발음들을 딕셔너리에 저장.
                                phonemes[nemes] += 1
                                print('nemes : ',nemes)
                            else:
                                phonemes[nemes] = 1
                    else:
                        phonemes["None"] += 1

    x, y = [], []
    for key in phonemes:
        if key != '.'and key != '?' and key != '!' and key != ',':
            x.append(key)
            y.append(phonemes[key])
    
    plt.figure()
    plt.rcParams["figure.figsize"] = (50, 20)
    plot = sns.barplot(x, y)
    if save_path:
        fig = plot.get_figure()
        fig.savefig(os.path.join(save_path, "phoneme_dist"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--train_file_path', required=True,
        help='this is the path to the train.txt file that the preprocess.py script creates'
    )
    parser.add_argument(
        '--save_to', help='path to save charts of data to'
    )
    parser.add_argument(
        '--cmu_dict_path', help='give cmudict-0.7b to see phoneme distribution' 
    )
    args = parser.parse_args()
    meta_data = process_meta_data(args.train_file_path)
    plt.rcParams["figure.figsize"] = (10, 5)
    plot(meta_data, save_path=args.save_to)
    if args.cmu_dict_path:
        plt.rcParams["figure.figsize"] = (30, 10)
        plot_phonemes(args.train_file_path, args.cmu_dict_path, args.save_to)
    
    plt.show()

if __name__ == '__main__':
    main()
