from random import randint
from mymodel import *
import copy

def create_gen_timetable(model_param, max_gen_count = 500, population_top=15, population_size=150): #pop_size = pop_top*(pop_top-1)/2
    DEBUG_LOGGER.info("create_gen_timetable: start")
    gen_count = 0
    max_tryings = int(max_gen_count/5)#50 #if we'll have no upgrades too long, we'll leave
    population = [copy.deepcopy(model_param) for _ in range(population_size)]
    max_population_cash = evaluate(model_param)
    best_model = model_param
    best_gen = -1
    trying_to_find_better_popul = max_tryings
    DEBUG_LOGGER.info(f"before genetic: last generation {gen_count} : cash {max_population_cash}: best generation {best_gen}")
    while gen_count<max_gen_count:
        mutate(population)
        top, top_1_cash=find_top(population, population_top)
        if max_population_cash<top_1_cash:
            best_model=copy.deepcopy(top[0])
            best_gen = gen_count
            max_population_cash = top_1_cash
            trying_to_find_better_popul = max_tryings
        else:
            trying_to_find_better_popul-=1
        if trying_to_find_better_popul==0:
            break
        population = multiply(top,population_size)
        if IS_DEBUG_MODE:
            DEBUG_LOGGER.debug(f"in-process: curr generation {gen_count} : cash {max_population_cash}: best generation {best_gen}")
        elif gen_count%int(max_gen_count/5) == int(max_gen_count/5)-1:
            DEBUG_LOGGER.debug(f"in-process: curr generation {gen_count} : cash {max_population_cash}: best generation {best_gen}")
        gen_count+=1
    DEBUG_LOGGER.info(f"after genetic: last generation {gen_count} : cash {max_population_cash}: best generation {best_gen}")
    DEBUG_LOGGER.info("create_gen_timetable: end")
    return best_model

def mutate(population):
    for model_id in range(len(population)):
        mutation_number = randint(1,5)
        for mut in range(mutation_number):
            mutation_type = int(randint(0,26)/3) #mutation 0: identity
                                     #mutation 1: delete shift rider
                                     #mutation 2: delete full rider
                                     #mutation 3: add shift rider
                                     #mutation 4: add full rider
                                     #mutation 5: move lunch for shift
                                     #mutation 6: move lunch for full
                                     #mutation 7: move start for shift
                                     #mutation 8: move start for full
            if mutation_type==1:
                population[model_id]["shift_riders_list"].pop(randint(0,len(population[model_id]["shift_riders_list"])-1))
                break
            elif mutation_type==2:
                population[model_id]["full_riders_list"].pop(randint(0,len(population[model_id]["full_riders_list"])-1))
                break
            elif mutation_type==3:
                population[model_id]["shift_riders_list"].append({"start_time":randint(0,(24-6+1)*12)*5, "lunch_time":randint(1,(24-6+1)*60/my_model._T_round)*my_model._T_round})
                break
            elif mutation_type==4:
                population[model_id]["full_riders_list"].append({"start_time":randint(0,(24-6+1)*12)*5, "lunch_time":randint(4*60/my_model._T_round,7*60/my_model._T_round)*my_model._T_round})
                break
            elif mutation_type==5:
                r_id = randint(0,len(population[model_id]["shift_riders_list"])-1)
                old_time_dict=population[model_id]["shift_riders_list"][r_id]
                flag, new_time = RiderShift.move_lunch_time_stat(old_time_dict)
                if not flag:
                    continue
                population[model_id]["shift_riders_list"][r_id]["lunch_time"] = new_time
                break
            elif mutation_type==6:
                r_id = randint(0,len(population[model_id]["full_riders_list"])-1)
                old_time_dict=population[model_id]["full_riders_list"][r_id]
                flag, new_time = RiderFull.move_lunch_time_stat(old_time_dict)
                if not flag:
                    continue
                population[model_id]["full_riders_list"][r_id]["lunch_time"] = new_time
                break
            elif mutation_type==7:
                r_id = randint(0,len(population[model_id]["shift_riders_list"])-1)
                old_time_dict=population[model_id]["shift_riders_list"][r_id]
                new_time = old_time_dict["start_time"]+randint(-12,12)*5
                if new_time<0:
                    new_time=0
                population[model_id]["shift_riders_list"][r_id]["start_time"] = new_time
                break
            elif mutation_type==8:
                r_id = randint(0,len(population[model_id]["full_riders_list"])-1)
                old_time_dict=population[model_id]["full_riders_list"][r_id]
                new_time = old_time_dict["start_time"]+randint(-12,12)*5
                if new_time<0:
                    new_time=0
                population[model_id]["full_riders_list"][r_id]["start_time"] = new_time
                break
            else:
                break

def find_top(population, population_top):
    top_id = [-1 for _ in range(population_top)]
    top_cash = [-1 for _ in range(population_top)]
    top_phase = 0
    top=[]
    for model_id in range(len(population)):
        cash = evaluate(population[model_id])
        if cash>top_cash[top_phase]:
            top_id[top_phase]=model_id
            top_cash[top_phase]=cash
            top_phase = (top_phase+1)%population_top
    top_1_cash = top_cash[(top_phase+population_top-1)%population_top]
    for i in range(population_top):
        top_phase = (top_phase+population_top-1)%population_top
        if top_id[top_phase]<0 or top_id[top_phase]>=len(population):
            continue
        top.append(population[top_id[top_phase]])
    return top, top_1_cash

def multiply(top, population_size):

    new_population = []
    for model_id in range(population_size):
        id_1 = randint(0,len(top)-1)
        id_2 = randint(0,len(top)-1)
        evol_dir = randint(1,100)%2
        new_model=copy.deepcopy(top[0])
        if evol_dir==0:
            new_model = copy.deepcopy(top[id_1])
        else:
            new_model = copy.deepcopy(top[id_2])
        evol_number = randint(2,6)
        for evol in range(evol_number):
            evol_param = int(randint(2,28)/4) #evol 0 - identity (2/4 of default chance)
                                               #evol 1 - add or delete 1 shift rider
                                               #evol 2 - add or delete 1 full rider
                                               #evol 3 - accept lunch for 1 shift rider
                                               #evol 4 - accept lunch for 1 full rider
                                               #evol 5 - accept start for 1 shift rider
                                               #evol 6 - accept start for 1 full rider
            if evol_param==1:
                len_id_1 = len(top[id_1]["shift_riders_list"])
                len_id_2 = len(top[id_2]["shift_riders_list"])
                if evol_dir==0:
                    len_id_1 = len(new_model["shift_riders_list"])
                    if len_id_1>len_id_2:
                        pop_ind = randint(0,len_id_1-1)
                        new_model["shift_riders_list"].pop(pop_ind)
                    elif len_id_1<len_id_2:
                        new_model["shift_riders_list"].append(top[id_2]["shift_riders_list"][randint(0,len_id_2-1)])
                else:
                    len_id_2 = len(new_model["shift_riders_list"])
                    if len_id_1<len_id_2:
                        pop_ind = randint(0,len_id_2-1)
                        new_model["shift_riders_list"].pop(pop_ind)
                    elif len_id_1>len_id_2:
                        new_model["shift_riders_list"].append(top[id_1]["shift_riders_list"][randint(0,len_id_1-1)])

            elif evol_param==2:
                len_id_1 = len(top[id_1]["full_riders_list"])
                len_id_2 = len(top[id_2]["full_riders_list"])
                if evol_dir==0:
                    len_id_1 = len(new_model["full_riders_list"])
                    if len_id_1>len_id_2:
                        pop_ind = randint(0,len_id_1-1)
                        new_model["full_riders_list"].pop(pop_ind)
                    elif len_id_1<len_id_2:
                        new_model["full_riders_list"].append(top[id_2]["full_riders_list"][randint(0,len_id_2-1)])
                else:
                    len_id_2 = len(new_model["full_riders_list"])
                    if len_id_1<len_id_2:
                        pop_ind = randint(0,len_id_2-1)
                        new_model["full_riders_list"].pop(pop_ind)
                    elif len_id_1>len_id_2:
                        new_model["full_riders_list"].append(top[id_1]["full_riders_list"][randint(0,len_id_1-1)])

            elif evol_param==3:
                rider_id = randint(0,len(new_model["shift_riders_list"])-1)
                if evol_dir==0:
                    if rider_id>len(top[id_2]["shift_riders_list"])-1:
                        continue
                    else:
                        new_model["shift_riders_list"][rider_id]["lunch_time"]=top[id_2]["shift_riders_list"][rider_id]["lunch_time"]
                else:
                    if rider_id>len(top[id_1]["shift_riders_list"])-1:
                        continue
                    else:
                        new_model["shift_riders_list"][rider_id]["lunch_time"]=top[id_1]["shift_riders_list"][rider_id]["lunch_time"]

            elif evol_param==4:
                rider_id = randint(0,len(new_model["full_riders_list"])-1)
                if evol_dir==0:
                    if rider_id>len(top[id_2]["full_riders_list"])-1:
                        continue
                    else:
                        new_model["full_riders_list"][rider_id]["lunch_time"]=top[id_2]["full_riders_list"][rider_id]["lunch_time"]
                else:
                    if rider_id>len(top[id_1]["full_riders_list"])-1:
                        continue
                    else:
                        new_model["full_riders_list"][rider_id]["lunch_time"]=top[id_1]["full_riders_list"][rider_id]["lunch_time"]

            elif evol_param==5:
                rider_id = randint(0,len(new_model["shift_riders_list"])-1)
                if evol_dir==0:
                    if rider_id>len(top[id_2]["shift_riders_list"])-1:
                        continue
                    else:
                        new_model["shift_riders_list"][rider_id]["start_time"]=top[id_2]["shift_riders_list"][rider_id]["start_time"]
                else:
                    if rider_id>len(top[id_1]["shift_riders_list"])-1:
                        continue
                    else:
                        new_model["shift_riders_list"][rider_id]["start_time"]=top[id_1]["shift_riders_list"][rider_id]["start_time"]

            elif evol_param==6:
                rider_id = randint(0,len(new_model["full_riders_list"])-1)
                if evol_dir==0:
                    if rider_id>len(top[id_2]["full_riders_list"])-1:
                        continue
                    else:
                        new_model["full_riders_list"][rider_id]["start_time"]=top[id_2]["full_riders_list"][rider_id]["start_time"]
                else:
                    if rider_id>len(top[id_1]["full_riders_list"])-1:
                        continue
                    else:
                        new_model["full_riders_list"][rider_id]["start_time"]=top[id_1]["full_riders_list"][rider_id]["start_time"]
        new_population.append(new_model)
    return new_population


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


def evaluate(model_params):
    model = my_model(**model_params)
    model_params["n_bus"] = update_buses(model)
    time = np.array(range(0,(24-6+1)*60,5))
    cash = 0
    total_cash = 0
    for day in range(1,8):
        ignore_rider = set()
        cooldown=day%3
        remainings = [0 for _ in range(0,model._T_max,5)]
        remainings_phase = 0
        cash=0
        model.create_queue_for_day(day>5)
        passanger_total_per_day = 0
        for t in time:
            if t<(24-6+1)*60:
                remainings[remainings_phase] = model.passangers_dict[t]
                passanger_total_per_day+=model.passangers_dict[t]
            remainings_phase= (remainings_phase +1)%len(remainings)
            for rn in range(len(model.riders_list)):#
                if rn in ignore_rider:
                    #riders_time[rn].append(-10)
                    continue
                if model.riders_list[rn].is_full():
                    if day>5:
                        continue
                    if model.riders_list[rn].is_working(t):
                        pass
                    else:
                        continue
                else:
                    if model.riders_list[rn].get_cooldown()==cooldown:
                        if model.riders_list[rn].is_working(t):
                            pass
                        else:
                            continue
                    else:
                        continue
                if not model.riders_list[rn].is_on_stop(t):
                    continue
                else:
                    if t>=(24-6+1)*60:
                        #riders_time[rn][-1]=-10
                        ignore_rider.add(rn)
                        continue
                #
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
                    if IS_DEBUG_MODE:
                        ERROR_LOGGER.error("gen: eval remaining <0 err")
                    for i in range(0,len(remainings)):
                        remainings[i]=0
        #
        cash*=model._ticket_price
        cash-=model.update_outcome()
        total_cash+=cash
    return total_cash