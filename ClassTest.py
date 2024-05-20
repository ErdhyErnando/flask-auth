# import argparse
# # import serial
# import multiprocessing as mp
# import time
# import datetime
# # import SharedArray as sa

# # Appending the relative path of the root folder
# # import sys, os


# class Test:
#     def __init__(self,Var1):

#         self.start = Var1

#         if len(sa.list()) != 0:
#             sa.delete("shm://out1")
#             sa.delete("shm://out2")
#             sa.delete("shm://flag")

#         self.out1    = sa.create("shm://out1",1)
#         self.out1[0] = Var1
#         self.out2   = sa.create("shm://out2",1)
#         self.out2[0] = Var1
#         self.flag = sa.create("shm://flag",1)
#         self.flag[0] = 0
        
#         pr_increase = mp.Process(target=self.increase)
#         pr_decrease = mp.Process(target=self.decrease)

#         pr_increase.start()
#         pr_decrease.start()

  
#     def increase(self):
#         while(self.out1[0]!=self.start+30):
#             self.out1[0] = self.out1[0] + 1 
#             if(self.out1[0]==self.start+30):
#                 self.flag[0] = 1
#             time.sleep(1)
    

#     def decrease(self):
#         self.out2[0] = self.out2[0] - 1 
#         time.sleep(1)

        