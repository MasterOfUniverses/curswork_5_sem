from mymodel import *

def create_manual_timetable(model: my_model): #we'll be trying to take all the people
    DEBUG_LOGGER.info("create_manual_timetable: start")
    predictable_cash = 0
    model.n_bus=0
    model.n_shift_r=0
    model.n_full_r=0
    model.riders_list.clear()
    weekend_day_cash=train_timetable_for_weekend(model)
    predictable_cash+=weekend_day_cash*8.7 #mean number of weekends
    workday_cash=train_timetable_for_workday(model)
    predictable_cash+=workday_cash*21.7 #mean number of work days
    if IS_DEBUG_MODE:
        DEBUG_LOGGER.debug(f"buses before update: {model.n_bus}")
    update_buses(model)
    if IS_DEBUG_MODE:
        DEBUG_LOGGER.debug(f"buses after update: {model.n_bus}")
    predictable_cash-=model.update_outcome()*30.4 #mean number of days (in month for 4 years)
    DEBUG_LOGGER.info(f"weekend: {weekend_day_cash} / workday: {workday_cash} / outcome: {model._predict_outcome}")
    DEBUG_LOGGER.info(f"predictable cash (mean): {int(predictable_cash)} per month: {int(predictable_cash/4.35)} per week")
    DEBUG_LOGGER.info("create_manual_timetable: end")

def train_timetable_for_weekend(model: my_model , cooldown = 0):
    model.create_queue_for_day(True)
    remainings = [0 for _ in range(0,model._T_max,5)]
    remainings_phase = 0
    time=0
    cash = 0
    #we'll optimize buses later
    for time in range(0,(24-6+1)*60,5):
        remainings[remainings_phase] = model.passangers_dict[time]
        remainings_phase= (remainings_phase +1)%len(remainings)
        for rn in range(len(model.riders_list)):
            if not model.riders_list[rn].is_on_stop(time):
                continue
            if model.riders_list[rn].is_full():
                if not model.riders_list[rn].is_working():
                    continue
            else:
                if not model.riders_list[rn].get_cooldown()==cooldown:
                    continue
            slots = model._bus_size
            for i in range(0,len(remainings)):
                slots-=remainings[(remainings_phase+i)%len(remainings)]
                cash+=remainings[(remainings_phase+i)%len(remainings)]
                remainings[(remainings_phase+i)%len(remainings)]=0
                if slots <=0:
                    remainings[(remainings_phase+i)%len(remainings)]=-slots
                    cash-=remainings[(remainings_phase+i)%len(remainings)]
                    slots=0
            if sum(remainings)<0:
                for i in range(0,len(remainings)):
                    remainings[i]=0
        #
        while sum(remainings)>=model._bus_size:
            model.riders_list.append(RiderShift(rider_id=len(model.riders_list),cooldown=0,start_time=time))
            model.riders_list.append(RiderShift(rider_id=len(model.riders_list),cooldown=1,start_time=time))
            model.riders_list.append(RiderShift(rider_id=len(model.riders_list),cooldown=2,start_time=time))
            model.n_shift_r+=3
            model.n_bus+=1

            slots = model._bus_size
            for i in range(0,len(remainings)):
                slots-=remainings[(remainings_phase+i)%len(remainings)]
                cash+=remainings[(remainings_phase+i)%len(remainings)]
                remainings[(remainings_phase+i)%len(remainings)]=0
                if slots <=0:
                    remainings[(remainings_phase+i)%len(remainings)]=-slots
                    cash-=remainings[(remainings_phase+i)%len(remainings)]
                    slots=0
        if remainings[remainings_phase]>0:
            model.riders_list.append(RiderShift(rider_id=len(model.riders_list),cooldown=0,start_time=time))
            model.riders_list.append(RiderShift(rider_id=len(model.riders_list),cooldown=1,start_time=time))
            model.riders_list.append(RiderShift(rider_id=len(model.riders_list),cooldown=2,start_time=time))
            model.n_shift_r+=3
            model.n_bus+=1
            cash+=sum(remainings)
            for i in range(0,len(remainings)):
                remainings[i]=0
        time+=5
    cash*=model._ticket_price
    return cash

def train_timetable_for_workday(model: my_model , cooldown = 0):
    model.create_queue_for_day(False)
    remainings = [0 for _ in range(0,model._T_max,5)]
    remainings_phase = 0
    time=0
    #we need bus-rider management here for "full" riders
    bus_for_full_queue=[] #stacking end_of_work time and after remove bus from this queue
    max_bus_queue_size=len(bus_for_full_queue)
    cash = 0
    for time in range(0,(24-6+1)*60,5):
        while len(bus_for_full_queue)>0 and time>=bus_for_full_queue[0]:
            bus_for_full_queue.pop(0)
        remainings[remainings_phase] = model.passangers_dict[time]
        remainings_phase= (remainings_phase +1)%len(remainings)
        for rn in range(len(model.riders_list)):
            if not model.riders_list[rn].is_on_stop(time):
                continue
            if model.riders_list[rn].is_full():
                if not model.riders_list[rn].is_working(time):
                    continue
            else:
                if not model.riders_list[rn].get_cooldown()==cooldown:
                    continue
            slots = model._bus_size
            for i in range(0,len(remainings)):
                slots-=remainings[(remainings_phase+i)%len(remainings)]
                cash+=remainings[(remainings_phase+i)%len(remainings)]
                remainings[(remainings_phase+i)%len(remainings)]=0
                if slots <=0:
                    remainings[(remainings_phase+i)%len(remainings)]=-slots
                    cash-=remainings[(remainings_phase+i)%len(remainings)]
                    slots=0
        #
        while sum(remainings)>=model._bus_size:
            model.riders_list.append(RiderFull(rider_id=len(model.riders_list),start_time=time))
            model.riders_list[-1].reverse_start_time()
            model.n_full_r+=1
            bus_for_full_queue.append(model.riders_list[-1].get_end_of_work())
            slots = model._bus_size
            for i in range(0,len(remainings)):
                slots-=remainings[(remainings_phase+i)%len(remainings)]
                cash+=remainings[(remainings_phase+i)%len(remainings)]
                remainings[(remainings_phase+i)%len(remainings)]=0
                if slots <=0:
                    remainings[(remainings_phase+i)%len(remainings)]=-slots
                    cash-=remainings[(remainings_phase+i)%len(remainings)]
                    slots=0
        if remainings[remainings_phase]>0:
            model.riders_list.append(RiderFull(rider_id=len(model.riders_list),start_time=time))
            model.riders_list[-1].reverse_start_time()
            model.n_full_r+=1
            bus_for_full_queue.append(model.riders_list[-1].get_end_of_work())
            cash+=sum(remainings)
            for i in range(0,len(remainings)):
                remainings[i]=0
        if len(bus_for_full_queue) > max_bus_queue_size:
            max_bus_queue_size = len(bus_for_full_queue)
    cash*=model._ticket_price
    model.n_bus+=max_bus_queue_size
    return cash

def update_buses(model:my_model):
    bus_queue=[] #stacking end_of_work time and after remove bus from this queue
    max_bus_queue_size=len(bus_queue)
    for t in range(0,(24-6+1)*60,5):
        while len(bus_queue)>0 and t>=bus_queue[0]:
            bus_queue.pop(0)
        for rider in model.riders_list:
            if not rider.is_full() and rider.get_cooldown()!=0:
                continue
            if not rider.is_working(t):
                continue
            if rider.is_on_stop(t):
                bus_queue.append(t+rider._trip_length)
        if len(bus_queue)>max_bus_queue_size:
            max_bus_queue_size=len(bus_queue)
    model.n_bus=max_bus_queue_size
    return model.n_bus
