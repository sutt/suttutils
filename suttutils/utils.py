import importlib
import types
import copy
import os
import site
import distutils.sysconfig as sysconfig

def _recurse_getattr(base, list_attrs):
    ''' 
        returns:
            a python object
        input 
            base -       python object
            list_attrs - list of strings for sub-attributes of base
        
        e.g. _recurse_get_attr(sklearn, ['metrics','r2_score']) -> r2_score
    '''
    attrs = copy.copy(list_attrs)
    if len(list_attrs) == 0: return base
    while(len(attrs) > 0):
        sub_attr = attrs.pop(0)
        try: 
            base = getattr(base, sub_attr)
        except:
            print(sub_attr)
            raise Exception('FailedGetAttr')
    return base    


def _build_skip_names():
    '''
        returns a list of strings for "reserved" python object names

        we want to skip these variables for recursive search in `walk_match`

        this function will likely fail on virtualenvs and unusualy installs of python
        
        there are three places where we can find these skip terms:
            - builtins
            - stdlib
            - site-packages

    '''

    builtin_names = dir(__builtins__)

    sitepkg_names = [fn.replace('.py','') 
                     for fn in os.listdir(site.getsitepackages()[0])
                     if '-' not in fn]

    stdlib_names = [e.replace('.py','') 
                    for e in os.listdir(sysconfig.get_python_lib(standard_lib=True))] 

    skip_names = builtin_names + sitepkg_names + stdlib_names

    return skip_names


def walk_match(search_term, 
               lib_name, 
               b_case_sensitive=True,
               b_skip=True, 
               b_print=True,
               max_depth=7):

    '''
        Search for a term in a package of interest. e.g.:

            >>> matches = walk_match('cnn', 'torchvision', b_case_sensitive=False)

        input:
            search_term       (str)     
            lib_name          (str)     package's import name
            b_case_sensitive  (bool)    search with case sensitivity
            b_skip            (bool)    skip over other pkgs / builtins/ stdlib
            b_print           (bool)    print results as we search
            max_depth         (int)     max attribute depth beneath top-level of pkg
                                        higher than 7 often fails to terminate

        output:
            each match (list of list of str) 
            
    '''
    
    global_match   = []
    clean_skip_names = [e for e in _build_skip_names() 
                        if search_term not in e]

    lib = importlib.import_module(lib_name)
    
    if b_case_sensitive: 
        def case(s): return s
    else: 
        def case(s): return s.lower()
    
    def inner(list_objs, depth_counter=0):
        
        nonlocal global_match
        nonlocal clean_skip_names

        obj = _recurse_getattr(lib, list_objs )

        def nonprivate(e):
            if len(e) < 1: return False
            return e[0] != '_'

        children = [e for e in dir(obj) if nonprivate(e)]

        for child in children:

            if b_skip:
                if child in clean_skip_names: 
                    continue

            sub_list_objs = copy.copy(list_objs)
            sub_list_objs += [child]

            if case(search_term) in case(child):
                global_match.append(sub_list_objs)
                if b_print: print(sub_list_objs)

            current = _recurse_getattr(lib, sub_list_objs)

            if isinstance(current, types.ModuleType):
                if depth_counter < max_depth:
                    inner(sub_list_objs, depth_counter + 1)
    
    inner([], 0)
    
    return global_match


### Testing ---------------

import warnings
import pytest

def test_recurse_getattr_1():
    try: 
        import spacy
        lib = spacy
    except:
        warnings.warn("Could not import `spacy` pkg; can't run test", UserWarning)
        return

    list_objs = []
    ret = _recurse_getattr(lib, list_objs)
    
    assert ret == spacy


def test_recurse_getattr_2():
    try: 
        import spacy
        lib = spacy
        import spacy.tokenizer
    except:
        warnings.warn("Could not import `spacy` pkg; can't run test", UserWarning)
        return

    list_objs = ['tokenizer']
    ret = _recurse_getattr(lib, list_objs)
    
    assert ret == spacy.tokenizer


def test_recurse_getattr_3():
    try: 
        import spacy
        lib = spacy
        from spacy.tokenizer import Tokenizer
    except:
        warnings.warn("Could not import `spacy` pkg; can't run test", UserWarning)
        return

    list_objs = ['tokenizer', 'Tokenizer']
    ret = _recurse_getattr(lib, list_objs)
    
    assert ret == Tokenizer


def test_walk_match_1():
    try: 
        import spacy
    except:
        warnings.warn("Could not import `spacy` pkg; can't run test", UserWarning)
        return 

    matches = walk_match('token', 'spacy', b_case_sensitive=True, max_depth=7)

    answers = [
        ['lang', 'tokenizer_exceptions'],
        ['pipeline', 'functions', 'merge_subtokens'],
        ['pipeline', 'merge_subtokens'],
        ['tokenizer'],
        ['tokens'],
        ['tokens', 'doc', 'Retokenizer'],
        ['tokens', 'token'],
    ]

    for answer in answers:
        assert answer in matches
    for match in matches:
        assert match in answers


def test_walk_match_2():
    try: 
        import spacy
    except:
        warnings.warn("Could not import `spacy` pkg; can't run test", UserWarning)
        return 

    matches = walk_match('token', 'spacy', b_case_sensitive=False, max_depth=7)

    answers = [
         ['analysis', 'Token']
        ,['gold', 'util', 'DummyTokenizer']
        ,['lang', 'punctuation', 'TOKENIZER_INFIXES']
        ,['lang', 'punctuation', 'TOKENIZER_PREFIXES']
        ,['lang', 'punctuation', 'TOKENIZER_SUFFIXES']
        ,['lang', 'tokenizer_exceptions']
        ,['lang', 'tokenizer_exceptions', 'TOKEN_MATCH']
        ,['language', 'TOKENIZER_INFIXES']
        ,['language', 'TOKENIZER_PREFIXES']
        ,['language', 'TOKENIZER_SUFFIXES']
        ,['language', 'TOKEN_MATCH']
        ,['language', 'Tokenizer']
        ,['language', 'util', 'DummyTokenizer']
        ,['matcher', 'matcher', 'TOKEN_PATTERN_SCHEMA']
        ,['matcher', 'phrasematcher', 'TOKEN_PATTERN_SCHEMA']
        ,['pipeline', 'functions', 'merge_subtokens']
        ,['pipeline', 'merge_subtokens']
        ,['pipeline', 'morphologizer', 'util', 'DummyTokenizer']
        ,['strings', 'util', 'DummyTokenizer']
        ,['syntax', 'nn_parser', 'util', 'DummyTokenizer']
        ,['syntax', 'transition_system', 'util', 'DummyTokenizer']
        ,['tokenizer']
        ,['tokenizer', 'Tokenizer']
        ,['tokenizer', 'util', 'DummyTokenizer']
        ,['tokens']
        ,['tokens', 'Token']
        ,['tokens', 'doc', 'Retokenizer']
        ,['tokens', 'doc', 'util', 'DummyTokenizer']
        ,['tokens', 'token']
        ,['tokens', 'token', 'Token']
        ,['tokens', 'token', 'util', 'DummyTokenizer']
        ,['util', 'DummyTokenizer']
        ,['vectors', 'util', 'DummyTokenizer']
        ,['vocab', 'util', 'DummyTokenizer']
    ]

    for answer in answers:
        assert answer in matches
    for match in matches:
        assert match in answers
