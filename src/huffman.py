import os
import sys
import time
import math
import queue
import argparse
import matplotlib.pyplot as plt

class BTNode:
    
    def __init__(self, symb:int=None, prob:float=0, lchild=None, rchild=None):
        self.symb = symb
        self.prob = prob
        self.lchild = lchild
        self.rchild = rchild
    
    def __lt__(self, rhs):
        assert isinstance(rhs, BTNode)
        return self.prob < rhs.prob
    

class Huffman:
    
    def __init__(self, bar=True):
        self._bar = bar
    
    def info(self, path:str):
        if not os.path.exists(path):
            print('Error: No such file')
            return None
        with open(path, 'rb') as fin:
            file_data = fin.read()
        file_size = len(file_data)
        file_stat = self._symb_stat(file_data, file_size)
        huffman_tree = self._construct_tree(file_stat)
        symb_dict = self._generate_dict(huffman_tree)
        hu = 0
        avg_n = 0
        for i, p in enumerate(file_stat):
            hu -= p * math.log2(p) if p != 0 else 0
            avg_n += p * len(symb_dict[i]) if p != 0 else 0
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
        if not os.path.exists(path):
            print('Error: No such file')
            return None
        with open(path, 'rb') as fin:
            file_data = fin.read()
        file_dir, file_name = os.path.split(path)
        file_size = len(file_data)
        file_stat = self._symb_stat(file_data, file_size)
        huffman_tree = self._construct_tree(file_stat)
        symb_dict = self._generate_dict(huffman_tree)
        dict_file = self._encode_dict(symb_dict)
        encoded_file = self._encode_file(file_data, file_size, symb_dict)
        with open(os.path.join(file_dir, file_name+'.hfp'), 'wb') as fout:
            fout.write(file_name.encode('utf-8') + bytes([0]))
            fout.write(file_size.to_bytes(math.ceil(math.ceil(math.log2(file_size))/8), byteorder='big') + bytes([0]))
            fout.write(dict_file)
            fout.write(encoded_file)
        if self._bar:
            print('')
        else:
            print('Encoding finished')
    
    def decode(self, path:str):
        if not os.path.exists(path):
            print('Error: No such file')
            return None
        if os.path.splitext(path)[-1] != '.hfp':
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
        inv_dict = dict()
        for i in range(256):
            symb_len = file_data[0]
            byte_len = math.ceil(symb_len/8)
            symb_str = format(int.from_bytes(file_data[1:1+byte_len], byteorder='big'), '0{:d}b'.format(8*byte_len))[:symb_len]
            file_data = file_data[1+byte_len:]
            inv_dict[symb_str] = i
        decoded_file = self._decode_file(file_data, file_size, inv_dict)
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
    
    def _construct_tree(self, symb_cnt:list) -> BTNode:
        prioque = queue.PriorityQueue()
        for i, p in enumerate(symb_cnt):
            prioque.put(BTNode(symb=i, prob=p))
        while prioque.qsize() != 1:
            lt = prioque.get()
            rt = prioque.get()
            pt = BTNode(prob=lt.prob+rt.prob, lchild=lt, rchild=rt)
            prioque.put(pt)
        return prioque.get()
    
    def _generate_dict(self, huffman_tree:BTNode) -> dict:
        encode_dict = dict()
        def traverse(node, code):
            if node.lchild is None and node.rchild is None:
                encode_dict[node.symb] = code
            else:
                traverse(node.lchild, code+'0')
                traverse(node.rchild, code+'1')
        traverse(huffman_tree, str())
        return encode_dict
    
    def _encode_dict(self, symb_dict:dict) -> bytes:
        encoded_dict = list()
        for i in range(256):
            code_str = symb_dict[i]
            encoded_dict.append(len(code_str))
            while len(code_str) > 0:
                if len(code_str) < 8:
                    code_str += '0' * (8-len(code_str))
                encoded_dict.append(int(code_str[:8], base=2))
                code_str = code_str[8:]
        return bytes(encoded_dict)
    
    def _encode_file(self, fdata:bytes, fsize:int, symb_dict:dict) -> bytes:
        encoded_str = str()
        encoded_file = list()
        for i, symb in enumerate(fdata):
            code = symb_dict[symb]
            encoded_str += code
            while len(encoded_str) >= 8:
                encoded_file.append(int(encoded_str[:8], base=2))
                encoded_str = encoded_str[8:]
            if self._bar and (i % (fsize//100) == 0 or i == fsize-1):
                ratio = int(50*(i+1)/fsize)
                sys.stdout.write("\rEncoding: ["+">"*ratio+" "*(50-ratio)+"] {}/{} {:.2f}%".format(i+1, fsize, 100*(i+1)/fsize))
                sys.stdout.flush()
        if len(encoded_str) > 0:
            encoded_file.append(int(encoded_str+'0'*(8-len(encoded_str)), base=2))
        return bytes(encoded_file)
    
    def _decode_file(self, fdata:bytes, fsize:int, inv_dict:dict) -> bytes:
        decoded_str = str()
        decoded_file = list()
        temp_str = str()
        k, i, j = 0, 0, 8
        while k != fsize:
            if j == 8:
                temp_str = format(fdata[i], '08b')
                i, j = i+1, 0
            decoded_str += temp_str[j]
            j += 1
            if decoded_str in inv_dict:
                decoded_file.append(inv_dict[decoded_str])
                k += 1
                decoded_str = str()
                if self._bar and (k % (fsize//100) == 0 or k == fsize):
                    ratio = int(50*k/fsize)
                    sys.stdout.write("\rDecoding: ["+">"*ratio+" "*(50-ratio)+"] {}/{} {:.2f}%".format(k, fsize, 100*k/fsize))
                    sys.stdout.flush()
        return bytes(decoded_file)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', type=str, required=True, help='Input File Path')
    parser.add_argument('-j', '--job', type=str, required=True, help='[encode, decode, eval]')
    parser.add_argument('-b', '--bar', type=bool, default=True, help='Show Process Bar')
    parser.add_argument('-i', '--info', type=bool, default=False, help='Display File Info (Only Eval Mode)')
    opt = parser.parse_args()
    huffman = Huffman(bar=opt.bar)
    if opt.job == 'encode':
        huffman.encode(opt.path)
    elif opt.job == 'decode':
        huffman.decode(opt.path)
    elif opt.job == 'eval':
        t0 = time.time()
        huffman.encode(opt.path)
        t1 = time.time()
        huffman.decode(opt.path+'.hfp')
        t2 = time.time()
        raw_size = os.path.getsize(opt.path)
        new_size = os.path.getsize(opt.path+'.hfp')
        if opt.info:
            huffman.info(opt.path)
        print('Encode Time: {:.5f}s'.format(t1-t0))
        print('Decode Time: {:.5f}s'.format(t2-t1))
        print('Raw Size: {:d}B'.format(raw_size))
        print('New Size: {:d}B'.format(new_size))
        print('Compress Rate: {:.2f}%'.format(new_size/raw_size*100))
        print('Encode Speed: {:.2f}KB/s'.format(raw_size/1024/(t1-t0)))
        print('Decode Speed: {:.2f}KB/s'.format(new_size/1024/(t2-t1)))
