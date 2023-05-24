from multiprocessing.pool import ThreadPool
from fuzzer import run,round,thread_count,testcase_dir,result_dir
import time
import shutil,os
from loguru import logger

def clean_dir():
    if os.path.exists(testcase_dir):
        shutil.rmtree(testcase_dir)
    if os.path.exists(result_dir):
        shutil.rmtree(result_dir)
    os.mkdir(testcase_dir)
    os.mkdir(result_dir)
    
def main():
    clean_dir()
    logger.info("[ExifFuzzer] Round: {}, Thread Count: {}, Start Success.".format(round,thread_count))
    start = time.time()
    pool = ThreadPool(thread_count)
    for count in range(round):
        pool.apply_async(run,(count,))
    pool.close()
    pool.join()
    end = time.time()
    logger.info("[ExifFuzzer] Finished in {} Second.".format(end-start))
    
if __name__ == '__main__':
    main()