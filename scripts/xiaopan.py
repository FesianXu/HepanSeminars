#!/usr/bin/python 
# -*- coding: utf-8 -*-  

# author: FesianXu
# 20210227
import json
import copy
import os
import sys
import argparse

UNK_MARK = ""
CATE_SPLIT_MARK = '.'
PAGES_MARK = '--'
CSV_SPLIT_MARK = ','
ROOT_MARK = "root"
REGISTER_CATE_JSON = '../papers_categories/register_categories.json'
CATE_TREE_PATH = '../papers_categories/categories_tree.txt'
JSON_LIST_PATH = "../papers_categories/json_list/"
CSV_TABLE_PATH = "../papers_categories/csv_tabls.csv"
PAPERS_POOL = "../papers_pool/"
PAPERS_DIST = "../papers_dist/"

def parse_file(name):
    with open(name, 'r', encoding='utf-8') as f:
        ret_dict = json.load(f)
    return ret_dict

class key_type_enum:
    required = "required"
    optional = "optional"
    
class key_dtype_enum:
    string = "string"
    list = "list"

class key_names:
    paper_names = "paper_names"
    alias = "alias"
    author = "authors"
    categories = "categories"
    year = "year"
    publisher = "publisher"
    pages = "pages"
    brief = "brief"
    blogs = "blogs"
    maintainers = "maintainers"
    download_link = "download_link"
    register_name = "register_name"

register_keys = [
    {"key_name": key_names.paper_names, "type": key_type_enum.required, "dtype": key_dtype_enum.string},
    {'key_name': key_names.register_name, "type": key_type_enum.optional, "dtype": key_dtype_enum.string},
    {"key_name": key_names.alias, "type": key_type_enum.optional, "dtype": key_dtype_enum.list},
    {"key_name": key_names.author, "type": key_type_enum.required, "dtype": key_dtype_enum.string},
    {"key_name": key_names.categories, "type": key_type_enum.required, "dtype": key_dtype_enum.list},
    {'key_name': key_names.year, "type": key_type_enum.required, "dtype": key_dtype_enum.string},
    {'key_name': key_names.publisher, "type": key_type_enum.required, "dtype": key_dtype_enum.string},
    {"key_name": key_names.pages, "type": key_type_enum.optional, "dtype": key_dtype_enum.string},
    {"key_name": key_names.brief, "type": key_type_enum.required, "dtype": key_dtype_enum.string},
    {"key_name": key_names.blogs, "type": key_type_enum.optional, "dtype": key_dtype_enum.list},
    {"key_name": key_names.maintainers, "type": key_type_enum.required, "dtype": key_dtype_enum.list},
    {"key_name": key_names.download_link, "type": key_type_enum.optional, "dtype": key_dtype_enum.string}
]
valid_year_range = [0,9999]
valid_keys = [x['key_name'] for x in register_keys]
required_keys = [x['key_name'] for x in register_keys if x['type'] == key_type_enum.required]
dtype_map = {}
for each in register_keys:
    dtype_map[each['key_name']] = each['dtype']


def _recur_builder(key, cate_tree, register_cates):
    if key in register_cates:
        cate_tree[key] = dict()
        cates = register_cates[key]
        for k,v in cates.items():
            if v == UNK_MARK:
                continue
            cate_tree[key][v] = dict()
            _recur_builder(v, cate_tree[key], register_cates)
        
    
def parse_register_cate_tree(json_file):
    cate_tree = dict()
    register_cates = parse_file(json_file)
    root_cates = register_cates['root']
    
    # appending root cates
    for rk, rv in root_cates.items():
        cate_tree[rv] = {}
    
    # recursively search the sub-categories of each root cate
    for rk, rv in cate_tree.items():
        _recur_builder(rk, cate_tree, register_cates)
    return cate_tree



def show(string):
    print("INFO:{}".format(string))

def _check_valid_pages(iv):
    if not (PAGES_MARK in iv):
        raise ValueError('The pages format error, should be begin_pages--end_pages, like 100--108')
    split_iv = iv.split(PAGES_MARK)
    begin_page = split_iv[0]
    end_page = split_iv[1]
    if '.' in begin_page:
        raise ValueError('begin page should be an integer, but got {}'.format(begin_page))
    if '.' in end_page:
        raise ValueError('end page should be an integer, but got {}'.format(begin_page))
    begin_page = int(begin_page)
    end_page = int(end_page)
    
    if begin_page < 0 or end_page < 0:
        raise ValueError('pages out of range! check the page to ensure it larger than 0!')
    if begin_page > end_page:
        raise ValueError('Woo, begin_pages should less than end_page, but now got {} > {}'.format(begin_page, end_page))
    return True

def _check_valid_year(iv):
    year = int(iv)
    if year < valid_year_range[0] or year > valid_year_range[1]:
        raise ValueError('The year valud should limited at the range of [{}, {}]'.format(valid_year_range[0], valid_year_range[1]))
    else:
        return True

def _check_valid_categories(cv):
    hier_cv = cv.split(CATE_SPLIT_MARK)
    tmp_tree = valid_cate_tree
    for each in hier_cv:
        if each in tmp_tree:
            tmp_tree = tmp_tree[each]
        else:
            raise ValueError('Category error with [{}]. INFO: The category [{}] is NOT in valid categories list. \
            Check your json or contact administer to append a new category!'.format(cv, each))
    return True

def check_info_valid(info, file_name, silence=False):
    assert isinstance(info, dict), 'Your json parsing result invalid, it should be a dict, check your json!'
    file_name = file_name.split('.')[0]
    key = list(info.keys())
    print("current process: [{}]".format(key[0]))
    # check whether the file name equal to json register key name
    if file_name != key[0]:
        raise ValueError('Your json register key name is [{}], while your file name is [{}]! They should be equal!'.format(key, file_name))
    
    # check if all required segments ready
    all_info_required_keys = set(copy.deepcopy(required_keys))
    for k,v in info.items():
        for ik, iv in v.items():
            if ik in all_info_required_keys:
                all_info_required_keys.remove(ik)
    if len(all_info_required_keys) != 0:
        raise ValueError("required fileds {} are missing! check again and commit!".format(str(all_info_required_keys)))
    
    # check all segments dtype valid
    for k,v in info.items():
        for ik, iv in v.items():
            if dtype_map[ik] == key_dtype_enum.list:
                if not isinstance(iv, dict):
                    raise ValueError('The segment {} is expected to be dtype of {}, but got a {}, check and commit again!'.format(key_dtype_enum.list, type(iv)))
    
    # check segments' content valid
    for k,v in info.items():
        
        for ik, iv in v.items():
            if ik not in valid_keys:
                raise ValueError("doc [{}] with key = [{}] is not in valid key list!".format(k, ik))
            
            if ik == key_names.categories:
                for ck,cv in iv.items():
                    _check_valid_categories(cv)
            if ik == key_names.year:
                _check_valid_year(iv)
            if ik == key_names.pages:
                _check_valid_pages(iv)
    if not silence:
        show("Thanks for your contribution ! This commit is valid! Please appending your paper in paper pools. (make sure your paper is open access.)")
    return True

def replace_comma(info):
    k = list(info.keys())[0]
    for ik,iv in info[k].items():
        if dtype_map[ik] == key_dtype_enum.string:
            info[k][ik] = info[k][ik].replace(",", ";")

def dump2csv(root_path, csv_name):
    all_jsons = os.listdir(root_path)
    f_write = open(csv_name, 'w', encoding='gbk')
    keys_len = len(register_keys)
    keys_seq = []
    for ind, each in enumerate(register_keys):
        title = each['key_name']
        keys_seq.append(title)
        f_write.write(title)
        if ind != keys_len-1:
            f_write.write(CSV_SPLIT_MARK)
    f_write.write('\n')
    
    for each in all_jsons:
        path = root_path+each
        paper_info = parse_file(path)
        check_info_valid(paper_info, each, silence=True)
        replace_comma(paper_info)
        for ind, each in enumerate(keys_seq):
            for k,v in paper_info.items():
                if each in v:
                    if dtype_map[each] != key_dtype_enum.list:
                        f_write.write(str(v[each]))
                    else:
                        f_write.write(str(v[each]).replace(",",";"))
                if each == key_names.register_name and each not in v:
                    f_write.write(k)
                if ind != keys_len-1:
                    f_write.write(CSV_SPLIT_MARK)
        f_write.write('\n')
    f_write.close()

def check_exists(all_jsons):
    title_names = {}
    for each in all_jsons:
        key = list(each.keys())[0]
        print("processing :[{}]".format(key))
        if key in title_names:
            raise ValueError('[{}] is duplicated! You may be adding a existed paper. Please use another register name'.format(key))
        title_names[key] = each[key][key_names.paper_names].strip().lower()
    # check the key name with all lower case
    keys_set = set()
    for k,v in title_names.items():
        if k.lower() in keys_set:
            raise ValueError("[{}] may be duplicated since the register name with lower case is duplicated!".format(k))
        else:
            keys_set.add(k.lower())
    
    # check the paper name
    paper_name_set = set()
    for k,v in title_names.items():
        if v in paper_name_set:
            raise ValueError('[{}], paper name is duplicated!'.format(v))
        else:
            paper_name_set.add(v)
        
def tree_hierachy(tree):
    stack = []
    tree = {ROOT_MARK: tree}
    stack.append((ROOT_MARK, tree, 0))
    depth_bound = {}
    while len(stack) != 0:
        cur_k, cur_v, depth = stack.pop()
        
        if depth in depth_bound:
            depth_bound[depth] = max(len(cur_k), depth_bound[depth])
        else:
            depth_bound[depth] = len(cur_k)
            
        keys = list(cur_v[cur_k].keys())
        keys.reverse() # make it begin from left, DLR
        for k in keys:
            v = {k: cur_v[cur_k][k]}
            stack.append((k, v, depth+1))
    return depth_bound
    

def draw_tree(tree, root_mark, root_path = './all_categories/', tree_name='papers_categories_tree.txt'):
    # pre-order 
    assert isinstance(tree, dict), 'your passing json tree should be a parsed dict, check your code !'
    if os.path.exists(tree_name):
        print('[Warning]: The tree name {} already existed, deleting it now!'.format(tree_name))
        os.system('rm -rf {}'.format(tree_name))
    if os.path.exists(root_path):
        print('[Warning]: The tmp folder {} already existed, deleting it now!'.format(root_path))
        os.system('rm -rf {}'.format(root_path))
        
    stack = []
    tree = {ROOT_MARK: tree}
    f_write = open('{}'.format(tree_name), 'w', encoding='utf-8')
    stack.append((root_mark, tree, 0, root_path+root_mark+'/'))
    while len(stack) != 0:
        cur_node = stack.pop()
        cur_k, cur_v, depth, last_folder = cur_node
        if not os.path.exists(last_folder):
            os.makedirs(last_folder)
        keys = list(cur_v[cur_k].keys())
        keys.reverse() # make it begin from left, DLR
        for k in keys:
            cur_folder = last_folder+k+'/'
            v = {k: cur_v[cur_k][k]}
            stack.append((k, v, depth+1, cur_folder))
    # make dirs
    os.system('tree {} > ./{}'.format(root_path, tree_name))
    os.system('rm -rf {}'.format(root_path))
    print('[Warning]: Deleted the tmp root folder {}!'.format(root_path))
    f_write.close()

def paper_dist(all_jsons):
    for each in all_jsons:
        cur_key = list(each.keys())[0]
        cates = each[cur_key][key_names.categories]
        paper_name = each[cur_key][key_names.paper_names].replace(":", "_")
        paper_name = paper_name.replace(" ", "_")
        print("Proccessing... [{}]".format(cur_key))
        for k, each_c in cates.items():
            src = PAPERS_POOL+cur_key+'.pdf'
            each_c = each_c.replace('.', "/")
            dst_folder = PAPERS_DIST+each_c+"/"
            if not os.path.exists(dst_folder):
                os.makedirs(dst_folder)
            dst_name = dst_folder+paper_name+'.pdf'    
            cmd = "cp {} {}".format(src, dst_name)
            os.system(cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check",action="store_true", help="Check the new submissions valid or not")
    parser.add_argument("--gen_catetree", action="store_true", help="Geneate the categories tree")
    parser.add_argument("--gen_csv", action="store_true", help="Geneate the papers csv table")
    parser.add_argument("--dist", action="store_true", help="Distribute the papers from pool to seperate folders")
    args = parser.parse_args()
    valid_cate_tree = parse_register_cate_tree(REGISTER_CATE_JSON)
    print('Current args {}'.format(args))

    if args.gen_catetree:
        tree = parse_register_cate_tree(REGISTER_CATE_JSON)
        draw_tree(tree, ROOT_MARK,root_path='../papers_categories/all_categories/', tree_name=CATE_TREE_PATH)
        print("Generate the categories tree at [{}]".format(CATE_TREE_PATH))
    if args.check:
        dirs = os.listdir(JSON_LIST_PATH)
        all_jsons = []
        for each in dirs:
            all_jsons.append(parse_file(JSON_LIST_PATH+each))
            
        check_exists(all_jsons)
        print("[SUCCESS] There is not duplication")

        for each in dirs:
            path = JSON_LIST_PATH+each 
            paper_info = parse_file(path)
            check_info_valid(paper_info, each, silence=True)
        print('[SUCCESS] Json information is valid')

    if args.gen_csv:
        dump2csv(JSON_LIST_PATH, CSV_TABLE_PATH)
        print('[SUCCESS] generate the csv table at {}'.format(CSV_TABLE_PATH))

    if args.dist:
        dirs = os.listdir(JSON_LIST_PATH)
        all_jsons = []
        for each in dirs:
            all_jsons.append(parse_file(JSON_LIST_PATH+each))
        paper_dist(all_jsons)
        print("[SUCCESS] The papers distributed to [{}] successed!".format(PAPERS_DIST))
    
    

    
