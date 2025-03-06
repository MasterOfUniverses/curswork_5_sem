from loggers import *
import json
import numpy as np
from datetime import datetime

class global_model(object): #task env
    __peek_coef = 7
    __normal_coef = 3
    __weekend_coef = 2

class my_model(object):
    def __init__(self, **kwargs):
        Rider._trip_length = self._T_round
        self.riders_list.clear()
        for key in kwargs:
            if key=="n_bus": #no match-case before 3.10, when having 3.9.13
                self.n_bus=kwargs[key]
            elif key=="shift_riders_list":
                self.n_shift_r = len(kwargs[key])*3
                for rider in kwargs[key]:
                    self.riders_list.append(RiderShift(len(self.riders_list),cooldown=0,start_time=rider["start_time"]))
                    self.riders_list[-1].set_lunch(rider["lunch_time"])
                    self.riders_list[-1].reverse_start_time()
                    self.riders_list.append(RiderShift(len(self.riders_list),cooldown=1,start_time=rider["start_time"]))
                    self.riders_list[-1].set_lunch(rider["lunch_time"])
                    self.riders_list[-1].reverse_start_time()
                    self.riders_list.append(RiderShift(len(self.riders_list),cooldown=2,start_time=rider["start_time"]))
                    self.riders_list[-1].set_lunch(rider["lunch_time"])
                    self.riders_list[-1].reverse_start_time()
            elif key=="full_riders_list":
                self.n_full_r = len(kwargs[key])
                for rider in kwargs[key]:
                    self.riders_list.append(RiderFull(len(self.riders_list),rider["start_time"]))
                    self.riders_list[-1].set_lunch(rider["lunch_time"])
                    self.riders_list[-1].reverse_start_time()
            else:
                continue
        self.update_outcome()

    __global_model = global_model()
    _bus_price = 31        #i started from bus=shift=2/3*full=1418, then full=2127.
    _salary_full = 65     #But it was too much, so i set bus about 2/3*1418 (31 per day),
    _salary_shift = 54    #full (65 per day instead of 71) and shift near 1600 (or 54 per day)
    _predict_outcome = 343#2060 #61800 #max_income = 138060 -> coef = 2.23. We'll be trying to stay with coef>2, cause for now it's the ideal
    _district_size_coef = 6 # use for nice values and for connection bus_size and global_model coef
    _ticket_price = 1
    _bus_size = 42
    _T_max = 20 #please, use 5-min step
    _T_round = 60 #u need upd in Rider
    n_bus = 0
    n_shift_r = 0  #*3
    n_full_r = 0   #*2
    def update_outcome(self):
        self._predict_outcome = self.n_bus*self._bus_price + self.n_full_r*self._salary_full+self._salary_shift*self.n_shift_r
        return self._predict_outcome
    def _print_model_params(self):
        return f"bus_size = {self._bus_size}\n"+f"n_bus = {self.n_bus}\n"+f"n_shift = {self.n_shift_r}\n"+f"n_full = {self.n_full_r}"
    riders_list = []
    def create_riders(self):
        self.update_outcome()
        self.riders_list.clear()
        for i in range(self.n_shift_r):
            self.riders_list.append(RiderShift(i,i%3))
        for j in range(self.n_shift_r, self.n_shift_r + self.n_full_r):
            self.riders_list.append(RiderFull(j))
    passangers_dict = dict()
    def create_queue_for_day(self,is_weekend=False): #be careful - quite many magic numbers for time in calculations
        self.passangers_dict.clear()
        if is_weekend:
            for t in range(0,(24-6+1)*60+1,5): #from 6:00 till 1:00
                self.passangers_dict[t] = self._my_model__global_model._global_model__weekend_coef * self._district_size_coef
        else:
            for t in range(0,(24-6+1)*60+1,5):
                if t>60 and t<3*60: #from 6:30 till 8:30
                    self.passangers_dict[t] = self._my_model__global_model._global_model__peek_coef * self._district_size_coef
                elif t>11*60 and t<13*60: #from 17:00 till 19:00
                    self.passangers_dict[t] = self._my_model__global_model._global_model__peek_coef * self._district_size_coef
                else:
                    self.passangers_dict[t] = self._my_model__global_model._global_model__normal_coef* self._district_size_coef
    def get_model_params(self):
        params={"n_bus":self.n_bus,
                "ticket_price":self._ticket_price
                }
        full_riders_list=[]
        shift_riders_list=[]
        for rider in self.riders_list:
            rider_param = {"start_time":rider._start_time,
                           "lunch_time":rider._lunch_time
                           }
            if rider.is_full():
                full_riders_list.append(rider_param)
            else:
                if rider.get_cooldown()==0:
                    shift_riders_list.append(rider_param)
        params["shift_riders_list"] = shift_riders_list
        params["full_riders_list"] = full_riders_list
        return params

#
class Rider(object):
    _rider_id=0
    _start_time=0 #minutes from 6:00
    _lunch_time=4*60 #minutes from start
    _trip_length = 60
    _break_length = 0
    def __init__(self, rider_id, start_time):
        self._rider_id = rider_id
        self._start_time = start_time
        self._lunch_time = 4*60
        self.reverse_lunch_time()

    def get_id(self):
        return self._rider_id
    def set_start(self, start_time):
        self._start_time = start_time
    def set_lunch(self,lunch_time):
        self._lunch_time=lunch_time
        self.reverse_lunch_time()
    def is_working(self, curr_time):
        pass
    def reverse_start_time(self):
        pass
    def is_full(self):
        return False
    def set_lunch(self, lunch_time):
        self._lunch_time = lunch_time #self._trip_length+(lunch_epoh-1)*(self._trip_length+self._break_length)
    def reverse_lunch_time(self): #good
        new_lunch_time=self._trip_length
        while new_lunch_time<self._lunch_time:
            new_lunch_time+=self._break_length+self._trip_length
        self._lunch_time = new_lunch_time #no set, because it'll be infinite cycle
    def move_lunch_time(self):
        if self._start_time+self._lunch_time+self._break_length+self._trip_length<self.get_end_of_work()-self._trip_length:
            self.set_lunch(self._lunch_time+self._break_length+self._trip_length)
            return True
        return False
    @staticmethod
    def move_lunch_time_stat(class_type,time_dict):
        if time_dict["start_time"]+time_dict["lunch_time"]+class_type._break_length+class_type._trip_length<class_type.get_end_of_work_stat()-class_type._trip_length:
            return True, time_dict["lunch_time"]+class_type._break_length+class_type._trip_length
        return False, time_dict["lunch_time"]
    def get_end_of_work(self):
        return (24-6+1)*60+1
    @staticmethod
    def get_end_of_work_stat():
        return (24-6+1)*60+1
    def is_on_stop(self,curr_time):
        curr_time-=self._start_time
        if curr_time>=self._lunch_time and curr_time<self._lunch_time+self._lunch_length:
            return False
        elif curr_time>= self._lunch_time+self._lunch_length:
            curr_time -= self._lunch_length + self._trip_length
        while curr_time>0:
            curr_time-=self._trip_length+self._break_length
        return curr_time == 0

class RiderFull(Rider):
    _lunch_length = 60
    _working_time = 8*60
    def is_working(self, curr_time):
        if self._start_time<=curr_time and curr_time<self._start_time+self._lunch_time:
            return 1
        elif self._start_time+self._lunch_time+self._lunch_length <= curr_time and curr_time<self._start_time+self._lunch_length+self._working_time:
            return 1
        else:
            return 0
    def is_full(self):
        return True
    def get_end_of_work(self):
        return self._start_time+self._lunch_length+self._working_time
    @staticmethod
    def get_end_of_work_stat():
        return RiderFull._working_time
    @staticmethod
    def move_lunch_time_stat(time_dict):
        if time_dict["start_time"]+time_dict["lunch_time"]+RiderFull._break_length+RiderFull._trip_length<RiderFull.get_end_of_work_stat()-RiderFull._trip_length:
            return True, time_dict["lunch_time"]+RiderFull._break_length+RiderFull._trip_length
        return False, time_dict["lunch_time"]
    def reverse_start_time(self):
        #if IS_DEBUG_MODE:
        #   DEBUG_LOGGER.debug(f"{(int(self._start_time/60)+6)%24}:{self._start_time%60}")
        if self._start_time>((24-6+1)-4)*60:
            new_time=4*60 #default lunch time
            if self._trip_length>new_time:
                new_time=self._trip_length
            self.set_lunch(new_time)
            new_time += self._lunch_length
            self.set_start(self._start_time - new_time)
            #if IS_DEBUG_MODE:
            #   DEBUG_LOGGER.debug(f"upd: {(int(self._start_time/60)+6)%24}:{self._start_time%60}")

class RiderShift(Rider):
    _cooldown = 0
    _lunch_length = 45
    _break_length = 15
    def __init__(self, rider_id, cooldown, start_time):
        super().__init__(rider_id,start_time)
        self._cooldown = cooldown
        self.reverse_start_time()

    def is_working(self, curr_time):#
        curr_time-=self._start_time
        count=0
        sum_time=0
        if curr_time<0:
            return 0
        if curr_time<self._lunch_time:
            while sum_time<=curr_time:
                count+=1
                if count%2 == 1:
                    sum_time+=self._trip_length
                else:
                    sum_time+=self._break_length
            return count%2
        elif curr_time<self._lunch_time+self._lunch_length:
            return 0
        else:
            sum_time+=self._lunch_time+self._lunch_length
            while sum_time<=curr_time:
                count+=1
                if count%2 == 1:
                    sum_time+=self._trip_length
                else:
                    sum_time+=self._break_length
            return count%2
    def get_cooldown(self): #?
        return self._cooldown
    def is_full(self):
        return False
    @staticmethod
    def get_end_of_work_stat():
        return (24-6+1)*60+1
    @staticmethod
    def move_lunch_time_stat(time_dict):
        if time_dict["start_time"]+time_dict["lunch_time"]+RiderShift._break_length+RiderShift._trip_length<RiderShift.get_end_of_work_stat()-RiderShift._trip_length:
            return True, time_dict["lunch_time"]+RiderShift._break_length+RiderShift._trip_length
        return False, time_dict["lunch_time"]
    def reverse_start_time(self): #error
        #if IS_DEBUG_MODE:
        #   DEBUG_LOGGER.debug(f"{(int(self._start_time/60)+6)%24}:{self._start_time%60}")
        old_time = self._start_time
        old_re = self.is_on_stop(old_time)
        if self._start_time>=self._trip_length+self._lunch_length:
            new_time = self._start_time-self._lunch_length-self._trip_length
            count=0
            while new_time>0:
                new_time-=self._trip_length+self._break_length
                count+=1
            new_time+=self._trip_length+self._break_length
            self.set_start(new_time)
            new_time = self._trip_length+(count-1)*(self._trip_length+self._break_length)
            self.set_lunch(new_time)






