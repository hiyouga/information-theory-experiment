import os
import sys
import time
import math
import argparse
import matplotlib.pyplot as plt

class LZ78:
    
    def __init__(self, bar=True):
        self._bar = bar
    
    def info(self, path:str):
        with open(path, 'rb') as fin:
            file_data = fin.read()
        file_size = len(file_data)
        file_stat = self._symb_stat(file_data, file_size)
        temp_bar = self._bar
        self._bar = False
        seg_dict, seg_list, seg_len = self._segmengtation(file_data, file_size)
        self._bar = temp_bar
        hu = 0
        for i, p in enumerate(file_stat):
            hu -= p * math.log2(p) if p != 0 else 0
        avg_n = len(seg_list) * (seg_len+8) / file_size
        xt = [i for i in range(256)]
        plt.figure()
        plt.bar(xt, file_stat)
        plt.title('Symbol distribution')
        plt.show()
        print('Average Len: {:.2f}'.format(avg_n))
        print('Entropy: {:.2f}'.format(hu))
        print('Expected Size: {:d}B'.format(math.ceil(avg_n * file_size / 8)))
        print('Ideal Size: {:d}B'.format(math.ceil(hu * file_size / 8)))
        print('Efficiency: {:.2f}%'.format(hu / avg_n * 100))
    
    def encode(self, path:str):
        with open(path, 'rb') as fin:
            file_data = fin.read()
        file_dir, file_name = os.path.split(path)
        file_size = len(file_data)
        seg_dict, seg_list, seg_len = self._segmengtation(file_data, file_size)
        encoded_file = self._encode_file(file_data, file_size, seg_dict, seg_list, seg_len)
        with open(os.path.join(file_dir, file_name+'.lzp'), 'wb') as fout:
            fout.write(file_name.encode('utf-8') + bytes([0]))
            fout.write(file_size.to_bytes(math.ceil(math.ceil(math.log2(file_size))/8), byteorder='big') + bytes([0]))
            fout.write(seg_len.to_bytes(math.ceil(math.ceil(math.log2(seg_len))/8), byteorder='big') + bytes([0]))
            fout.write(encoded_file)
        if self._bar:
            print('')
        else:
            print('Encoding finished')
    
    def decode(self, path:str):
        if os.path.splitext(path)[-1] != '.lzp':
            print('Error: Unknown File Type')
            return None
        with open(path, 'rb') as fin:
            file_data = fin.read()
        file_dir, _ = os.path.split(path)
        byte_idx = 0
        while file_data[byte_idx] != 0:
            byte_idx += 1
        file_name, file_data = file_data[:byte_idx], file_data[byte_idx+1:]
        byte_idx = 0
        while file_data[byte_idx] != 0:
            byte_idx += 1
        file_size, file_data = file_data[:byte_idx], file_data[byte_idx+1:]
        file_size = int.from_bytes(file_size, byteorder='big')
        byte_idx = 0
        while file_data[byte_idx] != 0:
            byte_idx += 1
        seg_len, file_data = file_data[:byte_idx], file_data[byte_idx+1:]
        seg_len = int.from_bytes(seg_len, byteorder='big')
        decoded_file = self._decode_file(file_data, file_size, seg_len)
        with open(os.path.join(file_dir, file_name.decode('utf-8')), 'wb') as fout:
            fout.write(decoded_file)
        if self._bar:
            print('')
        else:
            print('Decoding finished')
    
    def _symb_stat(self, fdata:bytes, fsize:int) -> list:
        symb_cnt = [0] * 256
        for symb in fdata:
            symb_cnt[symb] += 1
        for i in range(len(symb_cnt)):
            symb_cnt[i] /= fsize
        return symb_cnt
    
    def _segmengtation(self, fdata:bytes, fsize:int) -> tuple:
        seg_num = 0
        seg_dict = dict()
        seg_list = list()
        temp_str = str()
        for i, data in enumerate(fdata):
            temp_str += format(data, '08b')
            if temp_str not in seg_dict:
                seg_num += 1
                seg_dict[temp_str] = seg_num
                seg_list.append(temp_str)
                temp_str = str()
            if self._bar and ((i+1) % (fsize//50) == 0 or i == fsize-1):
                ratio = int(25*(i+1)/fsize)
                sys.stdout.write("\rEncoding: ["+">"*ratio+" "*(50-ratio)+"] {}/{} {:.2f}%".format((i+1)//2, fsize, 50*(i+1)/fsize))
                sys.stdout.flush()
        if len(temp_str) > 0:
            seg_list.append(temp_str)
        seg_len = math.ceil(math.log2(seg_num))
        return seg_dict, seg_list, seg_len
    
    def _encode_file(self, fdata:bytes, fsize:int, seg_dict:dict, seg_list:list, seg_len:int) -> bytes:
        encoded_file = list()
        encoded_str = str()
        t = 0
        for seg in seg_list:
            if len(seg) == 8:
                encoded_str += '0' * seg_len + seg
            else:
                encoded_str += format(seg_dict[seg[:-8]], '0{:d}b'.format(seg_len)) + seg[-8:]
            while len(encoded_str) >= 8:
                encoded_file.append(int(encoded_str[:8], base=2))
                encoded_str = encoded_str[8:]
            t += len(seg)//8
            if self._bar and (t % (fsize//50) == 0 or t == fsize):
                ratio = int(25+25*t/fsize)
                sys.stdout.write("\rEncoding: ["+">"*ratio+" "*(50-ratio)+"] {}/{} {:.2f}%".format((t+fsize)//2, fsize, 50+50*t/fsize))
                sys.stdout.flush()
        if len(encoded_str) > 0:
            encoded_file.append(int(encoded_str+'0'*(8-len(encoded_str)), base=2))
        return bytes(encoded_file)
    
    def _decode_file(self, fdata:bytes, fsize:int, seg_len:int) -> bytes:
        seg_list = list()
        decoded_file = list()
        temp_str = str()
        k, i = 0, 0
        while k != fsize:
            if len(temp_str) >= seg_len + 8:
                seg_str, sym_str = temp_str[:seg_len], temp_str[seg_len:seg_len+8]
                temp_str = temp_str[seg_len+8:]
                seg_val = int(seg_str, base=2)
                sym_val = int(sym_str, base=2)
                if seg_val == 0:
                    decoded_list = [sym_val]
                else:
                    decoded_list = seg_list[seg_val-1] + [sym_val]
                decoded_file += decoded_list
                seg_list.append(decoded_list)
                k += len(decoded_list)
                if self._bar and (k % (fsize//100) == 0 or k == fsize):
                    ratio = int(50*k/fsize)
                    sys.stdout.write("\rDecoding: ["+">"*ratio+" "*(50-ratio)+"] {}/{} {:.2f}%".format(k, fsize, 100*k/fsize))
                    sys.stdout.flush()
            else:
                temp_str += format(fdata[i], '08b')
                i += 1
        return bytes(decoded_file)
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', type=str, required=True, help='path of input file')
    parser.add_argument('-j', '--job', type=str, required=True, help='[encode, decode, eval]')
    parser.add_argument('-b', '--bar', type=bool, default=True, help='show process bar')
    parser.add_argument('-i', '--info', type=bool, default=False, help='display file info (only eval mode)')
    opt = parser.parse_args()
    if not os.path.exists(opt.path):
        print('Error: No such file')
    else:
        lz78 = LZ78(bar=opt.bar)
        if opt.job == 'encode':
            lz78.encode(opt.path)
        elif opt.job == 'decode':
            lz78.decode(opt.path)
        elif opt.job == 'eval':
            t0 = time.time()
            lz78.encode(opt.path)
            t1 = time.time()
            lz78.decode(opt.path+'.lzp')
            t2 = time.time()
            raw_size = os.path.getsize(opt.path)
            new_size = os.path.getsize(opt.path+'.lzp')
            if opt.info:
                lz78.info(opt.path)
            print('Encode Time: {:.5f}s'.format(t1-t0))
            print('Decode Time: {:.5f}s'.format(t2-t1))
            print('Raw Size: {:d}B'.format(raw_size))
            print('New Size: {:d}B'.format(new_size))
            print('Compress Rate: {:.2f}%'.format(new_size/raw_size*100))
            print('Encode Speed: {:.2f}KB/s'.format(raw_size/1024/(t1-t0)))
            print('Decode Speed: {:.2f}KB/s'.format(new_size/1024/(t2-t1)))
        else:
            print('Error: Unknown operation type')
