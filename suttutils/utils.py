import importlib
import types
import copy
import os
import site
import distutils.sysconfig as sysconfig

def recurse_getattr(base, list_attrs):
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


def build_skip_names():

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
    
    global_match   = []
    clean_skip_names = [e for e in build_skip_names() 
                        if search_term not in e]

    lib = importlib.import_module(lib_name)
    
    if b_case_sensitive: 
        def case(s): return s
    else: 
        def case(s): return s.lower()
    
    def inner(list_objs, depth_counter=0):
        
        nonlocal global_match
        nonlocal clean_skip_names

        obj = recurse_getattr(lib, list_objs )

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

            current = recurse_getattr(lib, sub_list_objs)

            if isinstance(current, types.ModuleType):
                if depth_counter < max_depth:
                    inner(sub_list_objs, depth_counter + 1)
    
    inner([], 0)
    
    return global_match