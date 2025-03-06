import matplotlib.pyplot as plt
from mymodel import *
from create_tt_manual import *
from create_tt_gen import *
#import copy #deep_copy is too heavy - we can only copy a short list of params in json-like dict and init new instance using this params
from platform import system

def plt_maximize():
    # See discussion: https://stackoverflow.com/questions/12439588/how-to-maximize-a-plt-show-window-using-python
    backend = plt.get_backend()
    cfm = plt.get_current_fig_manager()
    if backend == "wxAgg":
        cfm.frame.Maximize(True)
    elif backend == "TkAgg":
        if system() == "Windows":
            cfm.window.state("zoomed")  # This is windows only
        else:
            cfm.resize(*cfm.window.maxsize())
    elif backend == "QT4Agg":
        cfm.window.showMaximized()
    elif callable(getattr(cfm, "full_screen_toggle", None)):
        if not getattr(cfm, "flag_is_max", None):
            cfm.full_screen_toggle()
            cfm.flag_is_max = True
    else:
        raise RuntimeError("plt_maximize() is not implemented for current backend:", backend)
def print_and_evaluate_tt(model: my_model,figures_dict:dict, mode="Manual"):
    day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
    time = np.array(range(0,(24-6+1)*60+1+model._T_round,5))
    time_titles_base=[]
    time_titles=[]
    for t in time:
        hour=(6+int(t/60))%24
        minute = t%60
        title = "{hour:0>2d}:{minute:0>2d}".format(hour=hour, minute= minute)
        time_titles_base.append(title)
        if minute==0:
            time_titles.append(title)
    #time_titles = np.array(time_titles_base)
    cash = 0
    total_cash = 0
    total_passangers=0
    catched_passangers=0
    bus_tt_dict = {}
    fig_for_all = plt.figure(num=f"{mode} mode: all",figsize=(100, 18), dpi= 240, facecolor='w', edgecolor='k')
    for day in range(1,8):
        ignore_rider = set()
        fig_for_day = plt.figure(num=f"{mode} mode: {day_names[day]}",figsize=(32, 18), dpi= 240, facecolor='w', edgecolor='k')
        cooldown=day%3
        queue_size = []
        riders_time = [[] for i in range(len(model.riders_list))]
        bus_tt = []
        remainings = [0 for _ in range(0,model._T_max,5)]
        remainings_phase = 0
        cash=0
        model.create_queue_for_day(day>5)
        passanger_total_per_day = 0
        for t in time:
            if t<(24-6+1)*60:
                remainings[remainings_phase] = model.passangers_dict[t]
                passanger_total_per_day+=model.passangers_dict[t]
            else:
                remainings=[0 for _ in range(0,model._T_max,5)]
            remainings_phase= (remainings_phase +1)%len(remainings)
            for rn in range(len(model.riders_list)):#
                if rn in ignore_rider:
                    riders_time[rn].append(-10)
                    continue
                if model.riders_list[rn].is_full():
                    if day>5:
                        riders_time[rn].append(-10)
                        continue
                    if model.riders_list[rn].is_working(t):
                        riders_time[rn].append(rn)
                    else:
                        riders_time[rn].append(-10)
                        continue
                else:
                    if model.riders_list[rn].get_cooldown()==cooldown:
                        if model.riders_list[rn].is_working(t):
                            riders_time[rn].append(rn)
                        else:
                            riders_time[rn].append(-10)
                            continue
                    else:
                        riders_time[rn].append(-10)
                        continue
                if not model.riders_list[rn].is_on_stop(t):
                    continue
                else:
                    if t>=(24-6+1)*60:
                        riders_time[rn][-1]=-10
                        ignore_rider.add(rn)
                        continue
                    bus_tt.append("{hour:0>2d}:{minute:0>2d}".format(hour=(int(t/60)+6)%24, minute = t%60))
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
            queue_size.append(sum(remainings))
        #
        bus_tt_dict[day_names[day]] = bus_tt
        catched_passangers+=cash
        cash*=model._ticket_price
        cash-=model.update_outcome()

        rider_plt_total = fig_for_all.add_subplot(2, 7, day)
        queue_plt_total = fig_for_all.add_subplot(2, 7, 7+day)

        rider_plt_for_day=fig_for_day.add_subplot(2, 1, 1)
        queue_plt_for_day=fig_for_day.add_subplot(2, 1, 1+1)
        for rn in range(len(model.riders_list)):
            rider_plt_for_day.scatter(time_titles_base, np.array(riders_time[rn]), marker="o")
            rider_plt_total.scatter(time_titles_base, np.array(riders_time[rn]), marker="o")
        queue_plt_for_day.plot(time_titles_base,queue_size)
        queue_plt_total.plot(time_titles_base,queue_size)

        total_cash+=cash
        total_passangers+=passanger_total_per_day

        queue_plt_for_day.grid(color='0.95',linestyle='-')
        queue_plt_total.grid(color='0.95',linestyle='-')
        rider_plt_for_day.grid(color='0.95',linestyle='-')
        rider_plt_total.grid(color='0.95',linestyle='-')
        queue_plt_total.set_title(f"{day_names[day]}. Total cash: {cash}")
        queue_plt_for_day.set_title(f"{day_names[day]}. Total cash: {cash}")
        rider_plt_for_day.set_ylim(-1, None)
        rider_plt_total.set_ylim(-1, None)
        rider_plt_for_day.set_xticks(time_titles)
        rider_plt_total.set_xticks([time_titles[i] for i in range(0,len(time_titles),2)])
        queue_plt_total.set_xticks([time_titles[i] for i in range(0,len(time_titles),2)])
        queue_plt_for_day.set_xticks(time_titles)
        queue_plt_total.set_xlim(None, "01:20")
        queue_plt_for_day.set_xlim(None, "01:20")
        figures_dict[f"{mode}_mode_{day_names[day]}.png"]=fig_for_day
    figures_dict[f"{mode}_mode_all.png"]=fig_for_all
    OUTPUT_LOGGER.info(json.dumps(bus_tt_dict, indent=4))
    OUTPUT_LOGGER.info(f"total passangers {total_passangers} / catched passangers {catched_passangers} / total cash {total_cash}")

def pretty_time_for_print(model_param:dict):
    for key in model_param:
        key=""
        if key.find("_riders_list")!=-1:
            for i in len(model_param[key]):
                old_start_time = model_param[key][i]["start_time"]
                pretty_start_time = "{hour:0>2d}:{minute:0>2d}".format(hour=(int(old_start_time/60)+6)%24, minute = old_start_time%60)
                old_lunch_time = model_param[key][i]["lunch_time"]
                new_lunch_time = old_start_time+old_lunch_time
                pretty_lunch_time = "{hour:0>2d}:{minute:0>2d}".format(hour=(int(new_lunch_time/60)+6)%24, minute = new_lunch_time%60)
                model_param[key][i]["start_time"]=pretty_start_time
                model_param[key][i]["lunch_time"]=pretty_lunch_time
        else:
            continue
    return model_param

def save_figures(figures_dict:dict):
    for name in  figures_dict:
        figures_dict[name].savefig(f"{name}")

def main():
    figures_dict=dict({})
    model = my_model()
    create_manual_timetable(model)
    print_and_evaluate_tt(model, figures_dict)
    model_for_gen = model.get_model_params()
    model_from_gen = create_gen_timetable(model_for_gen)
    print_and_evaluate_tt(my_model(**model_from_gen), figures_dict,mode="Genetics")
    OUTPUT_LOGGER.info("manual:\n"+json.dumps(pretty_time_for_print(model_for_gen), indent=4))
    OUTPUT_LOGGER.info("gen:\n"+json.dumps(pretty_time_for_print(model_from_gen), indent=4))
    #plt_maximize()
    save_figures(figures_dict)
    plt.show()

main()