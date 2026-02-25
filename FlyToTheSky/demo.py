import os
import shutil
import time
import random
import psutil
import subprocess

ps = None

def send(src, des):
    src_file_list = os.listdir(src)
    print("{} files found".format(len(src_file_list)))
    for idx, src_file in enumerate(src_file_list):
        delay = random.randint(500, 1500)/1000
        time.sleep(delay)
        shutil.copy(os.path.join(src, src_file), os.path.join(des, src_file))
        print("{} send, {} delayed".format(idx+1, delay))
    print("done")

def get_procs():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        processes.append(proc.info)
    
    return processes

def exit_proc(name):
    try:
        for pid in [x['pid'] for x in get_procs() if 'python' in x['name']]:
            me = psutil.Process(pid)
            if me == None:
                continue
            if me.parent() == None:
                continue
            if me.parent().pid == ps:
                me.terminate()
                print("terminate children. pid = {}".format(pid))
        if ps != None:
            proc = psutil.Process(ps)
            proc.terminate()
            print("terminate current program. pid = {}".format(ps))
    except psutil.NoSuchProcess:
        print("No proc found with name: {}".format(name))
    except psutil.AccessDenied:
        print("Accesss Denied.")

def reset():
    global ps
    exit_proc("python")
    try:
        
        shutil.rmtree(r"C:\Users\yuilhae\yuilhaePNU\graduation\yard_manage_program\datas")
        print("clear old data.")
    except FileNotFoundError:
        pass
    src = r"C:\Users\yuilhae\yuilhaePNU\graduation\yard_manage_program\datas_origin"
    des = r"C:\Users\yuilhae\yuilhaePNU\graduation\yard_manage_program\datas"
    shutil.copytree(src, des)
    print("set initial data.")

    try:
        command = "conda activate graduation && python C:/Users/yuilhae/yuilhaePNU/graduation/yard_manage_program/main.py"
        pr = subprocess.Popen(['cmd', '/c', command], stdout=subprocess.DEVNULL)
        ps = pr.pid
        print("launch new project program. pid = {}".format(ps))
    except Exception as e:
        print("error", e)


#################################

map_name_list = ["bongam1", "bongam2", "dekgok1", "deokgok2", "hannae", "hmps", "obee"]
drone_src = r"C:\Users\yuilhae\yuilhaePNU\graduation\yard_manage_program\ret_temp"
drone_des = r"C:\Users\yuilhae\yuilhaePNU\graduation\yard_manage_program\datas\retrieved_patch"

#################################

print("="*75)
print("\n{:^75}".format("graduation project"))
print("{:^75}\n".format("presentator"))
print("="*75)
print("")
print(" "*2, "USAGE:")
print(" "*5, "COM  : description\n")
print(" "*5, "start: launch the program")
print(" "*5, "reset: reset data, re-start the program")
print(" "*5, "map  : load map datas, valid maps above")
print(" "*12, "{}".format(", ".join(map_name_list)))
print("")

l = get_procs()

while True:
    map_name = input("="*75 + "\nEnter: ")
    if map_name == "reset" or map_name == "start":
        reset()
        
        print("done")
    elif map_name == "exit":
        print("exit...")
        exit()
    elif map_name in map_name_list:
        print("load {} data".format(map_name))
        send(os.path.join(drone_src, map_name), os.path.join(drone_des, map_name))
    else:
        print("An undefined command. {}".format(map_name))

