import calendar
import itertools
import logging
import collections
from random import randint, choice
from datetime import datetime, timedelta, time
from dateutil.parser import parse
from django import http
from django.db import models
from django.db import connection as dbconnection
#print "dbc0:", len(dbconnection.queries)
from django.template.context import RequestContext
from django.shortcuts import get_object_or_404, render, redirect,HttpResponseRedirect,render_to_response
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
#from django.forms import modelformset_factory

from swingtime.models import Event, Occurrence
#from swingtime.models import Occurrence
from swingtime import utils, forms
from swingtime.conf import settings as swingtime_settings

from con_event.models import Con
from con_event.forms import ConSchedStatusForm
from scheduler.models import Location, Training, Challenge
from scheduler.forms import ChalStatusForm,TrainStatusForm,CInterestForm,TInterestForm,ActCheck
from swingtime.forms import DLCloneForm,SlotCreate,L1Check

from dateutil import parser

import django_tables2 as tables
from scheduler.tables import ChallengeTable,TrainingTable
from django_tables2  import RequestConfig

if swingtime_settings.CALENDAR_FIRST_WEEKDAY is not None:
    calendar.setfirstweekday(swingtime_settings.CALENDAR_FIRST_WEEKDAY)


#-------------------------------------------------------------------------------
@login_required
def chal_submit(
    request,
    template='swingtime/chal_submit.html',
    con_id=None,
    **extra_context
):

    if con_id:
        con=Con.objects.get(pk=con_id)
    else:
        con=Con.objects.most_upcoming()

    q=Challenge.objects.filter(con=con, RCrejected=False).exclude(roster1=None).exclude(roster2=None).exclude(submitted_on=None).order_by('submitted_on')
    q_od  = collections.OrderedDict()
    data=[]
    for c in q:
        thisdict={"name":c,"gametype":c.get_gametype_display(),"location_type":c.location_type,"duration":c.get_duration_display(),"submitted_on":c.submitted_on}
        form=ChalStatusForm(request.POST or None, instance=c,prefix=str(c.pk))
        thisdict["status"]=form
        data.append(thisdict)
        q_od[c]=form

    save_success=0
    if request.method == 'POST':
        for form in q_od.values():
            if form.is_valid():
                this_instance=form.save()
                save_success+=1
        for dic in data:
            chal=dic.get("name")
            if chal.RCrejected==True:
                data.remove(dic)

    table = ChallengeTable(data)
    #RequestConfig(request).configure(table)
    RequestConfig(request,paginate={"per_page": 300}).configure(table)


    new_context={"table":table,"save_success":save_success,"q_od":q_od,"con":con,"con_list":Con.objects.all()}
    extra_context.update(new_context)
    return render(request, template, extra_context)

#-------------------------------------------------------------------------------
@login_required
def chal_accept(
    request,
    template='swingtime/chal_accept.html',
    con_id=None,
    **extra_context
):

    if con_id:
        con=Con.objects.get(pk=con_id)
    else:
        con=Con.objects.most_upcoming()

    q=Challenge.objects.filter(con=con, RCaccepted=True).exclude(submitted_on=None).order_by('submitted_on')
    q_od = collections.OrderedDict()
    data=[]
    for c in q:
        thisdict={"name":c,"gametype":c.get_gametype_display(),"location_type":c.location_type,"duration":c.get_duration_display(),"submitted_on":c.submitted_on}
        form=ChalStatusForm(request.POST or None, instance=c,prefix=str(c.pk))
        thisdict["status"]=form
        data.append(thisdict)
        q_od[c]=form

    save_success=0
    if request.method == 'POST':
        for form in q_od.values():
            if form.is_valid():
                this_instance=form.save()
                save_success+=1
                # if this_instance.RCaccepted==False:
                #     del q_od[this_instance]#remove if no longer accepted
            for dic in data:
                chal=dic.get("name")
                if chal.RCaccepted==False:
                    data.remove(dic)

    table = ChallengeTable(data)
    #RequestConfig(request).configure(table)
    RequestConfig(request,paginate={"per_page": 300}).configure(table)
    new_context={'table':table,"save_success":save_success,"q_od":q_od,"con":con,"con_list":Con.objects.all()}
    extra_context.update(new_context)
    return render(request, template, extra_context)

#-------------------------------------------------------------------------------
@login_required
def chal_reject(
    request,
    template='swingtime/chal_reject.html',
    con_id=None,
    **extra_context
):

    if con_id:
        con=Con.objects.get(pk=con_id)
    else:
        con=Con.objects.most_upcoming()

    q=Challenge.objects.filter(con=con, RCrejected=True).exclude(submitted_on=None).order_by('submitted_on')
    q_od = collections.OrderedDict()
    data=[]
    for c in q:
        thisdict={"name":c,"gametype":c.get_gametype_display(),"location_type":c.location_type,"duration":c.get_duration_display(),"submitted_on":c.submitted_on}
        form=ChalStatusForm(request.POST or None, instance=c,prefix=str(c.pk))
        thisdict["status"]=form
        data.append(thisdict)
        q_od[c]=form

    save_success=0
    if request.method == 'POST':
        for form in q_od.values():
            if form.is_valid():
                this_instance=form.save()
                save_success+=1
            for dic in data:
                chal=dic.get("name")
                if chal.RCrejected==False:
                    data.remove(dic)
                # if this_instance.RCrejected==False:
                #     del q_od[this_instance]#remove if no longer accepted

    table = ChallengeTable(data)
    #RequestConfig(request).configure(table)
    RequestConfig(request,paginate={"per_page": 300}).configure(table)
    new_context={"table":table,"save_success":save_success,"q_od":q_od,"con":con,"con_list":Con.objects.all()}
    extra_context.update(new_context)
    return render(request, template, extra_context)

#-------------------------------------------------------------------------------

@login_required
def train_submit(
    request,
    template='swingtime/train_submit.html',
    con_id=None,
    **extra_context
):

    if con_id:
        con=Con.objects.get(pk=con_id)
    else:
        con=Con.objects.most_upcoming()

    q=Training.objects.filter(con=con, RCrejected=False).order_by('created_on')
    q_od  = collections.OrderedDict()
    data=[]
    for c in q:
        thisdict={"name":c,"coach":c.display_coach_names(),"skill":c.registered.skill_display(),"onsk8s":c.onsk8s,"contact":c.contact,
            "location_type":c.location_type,"duration":c.get_duration_display(),"created_on":c.created_on}
        form=TrainStatusForm(request.POST or None, instance=c,prefix=str(c.pk))
        thisdict["status"]=form
        data.append(thisdict)
        q_od[c]=form

    save_success=0
    if request.method == 'POST':
        for form in q_od.values():
            if form.is_valid():
                this_instance=form.save()
                save_success+=1
        for dic in data:
            train=dic.get("name")
            if train.RCrejected==True:
                data.remove(dic)
                # if this_instance.RCrejected==True:
                #     del q_od[this_instance]#remove if no longer accepted

    table = TrainingTable(data)
    #RequestConfig(request).configure(table)
    RequestConfig(request,paginate={"per_page": 300}).configure(table)

    new_context={"table":table,"save_success":save_success,"q_od":q_od,"con":con,"con_list":Con.objects.all()}
    extra_context.update(new_context)
    return render(request, template, extra_context)

#-------------------------------------------------------------------------------
@login_required
def train_accept(
    request,
    template='swingtime/train_accept.html',
    con_id=None,
    **extra_context
):

    if con_id:
        con=Con.objects.get(pk=con_id)
    else:
        con=Con.objects.most_upcoming()

    q=Training.objects.filter(con=con, RCaccepted=True).order_by('created_on')
    q_od = collections.OrderedDict()
    data=[]
    for c in q:
        thisdict={"name":c,"coach":c.display_coach_names(),"skill":c.registered.skill_display(),"onsk8s":c.onsk8s,"contact":c.contact,
            "location_type":c.location_type,"duration":c.get_duration_display(),"created_on":c.created_on}
        form=TrainStatusForm(request.POST or None, instance=c,prefix=str(c.pk))
        thisdict["status"]=form
        data.append(thisdict)
        q_od[c]=form

    save_success=0
    if request.method == 'POST':
        for form in q_od.values():
            if form.is_valid():
                this_instance=form.save()
                save_success+=1
        for dic in data:
            train=dic.get("name")
            if train.RCaccepted==False:
                data.remove(dic)
                # if this_instance.RCaccepted==False:
                #     del q_od[this_instance]#remove if no longer accepted


    table = TrainingTable(data)
    #RequestConfig(request).configure(table)
    RequestConfig(request,paginate={"per_page": 300}).configure(table)

    new_context={"table":table,"save_success":save_success,"q_od":q_od,"con":con,"con_list":Con.objects.all()}
    extra_context.update(new_context)
    return render(request, template, extra_context)

#-------------------------------------------------------------------------------
@login_required
def train_reject(
    request,
    template='swingtime/train_reject.html',
    con_id=None,
    **extra_context
):

    if con_id:
        con=Con.objects.get(pk=con_id)
    else:
        con=Con.objects.most_upcoming()

    q=Training.objects.filter(con=con, RCrejected=True).order_by('created_on')
    q_od = collections.OrderedDict()
    data=[]
    for c in q:
        thisdict={"name":c,"coach":c.display_coach_names(),"skill":c.registered.skill_display(),"onsk8s":c.onsk8s,"contact":c.contact,
            "location_type":c.location_type,"duration":c.get_duration_display(),"created_on":c.created_on}
        form=TrainStatusForm(request.POST or None, instance=c,prefix=str(c.pk))
        thisdict["status"]=form
        data.append(thisdict)
        q_od[c]=form

    save_success=0
    if request.method == 'POST':
        for form in q_od.values():
            if form.is_valid():
                this_instance=form.save()
                save_success+=1
        for dic in data:
            train=dic.get("name")
            if train.RCrejected==False:
                data.remove(dic)
                # if this_instance.RCrejected==False:
                #     del q_od[this_instance]#remove if no longer accepted

    table = TrainingTable(data)
    #RequestConfig(request).configure(table)
    RequestConfig(request,paginate={"per_page": 300}).configure(table)

    new_context={"table":table,"save_success":save_success,"q_od":q_od,"con":con,"con_list":Con.objects.all()}
    extra_context.update(new_context)
    return render(request, template, extra_context)

#-------------------------------------------------------------------------------

@login_required
def act_unsched(
    request,
    template='swingtime/act_unsched.html',
    con_id=None,
    **extra_context
):
    if con_id:
        con=Con.objects.get(pk=con_id)
    else:
        con=Con.objects.most_upcoming()

    activities=[]
    level1pairs={}
    save_attempt=False
    save_success=False
    added2schedule=[]
    act_types=["challenge","training"]
    prefix_base=""
    cycle=-1
    possibles=[]


    if request.method == 'POST':
        post_keys=dict(request.POST).keys()
        #print request.POST

        if 'Auto_Chal' in request.POST or 'Auto_Train' in request.POST:
            pk_list=[]
            activities=[]
            possible_dicts={}
            act_tups=[]
            o_dicts={}
            o_tups=[]

            taken_os=[] #only necessary if i make it choose randomly

            if 'Auto_Chal' in request.POST:
                for k in post_keys:
                    lsplit=k.split("-")
                    prefix_base='challenge'
                    if lsplit[0]==prefix_base:
                        pk_list.append(int(lsplit[1]))
                possibles=Challenge.objects.filter(pk__in=pk_list)
            elif 'Auto_Train' in request.POST:
                for k in post_keys:
                    lsplit=k.split("-")
                    prefix_base='training'
                    if lsplit[0]==prefix_base:
                        pk_list.append(int(lsplit[1]))
                possibles=Training.objects.filter(pk__in=pk_list)

            for a in possibles:
                level1find,level1halffind, level2find,level3find=a.find_level_slots()
                pos_dict={1:level1find,1.5:level1halffind,2:level2find,3:level3find}
                possible_dicts[a]=pos_dict
                act_tups.append((a,len(level1find),len(level1halffind),len(level2find),len(level3find)))

#########temporarily making o choice randon#######
            #     for o in level1find:
            #         if o not in o_dicts:
            #             o_dicts[o]=1
            #         else:
            #             tempi=o_dicts.get(o)
            #             tempi+=1
            #             o_dicts[o]=tempi
            #
            # for k,v in o_dicts.iteritems():
            #     o_tups.append((k,v))
            #
            # sorted(act_tups, key=lambda x: x[1])#sorts by second paramter, level1finds
            # sorted(o_tups, key=lambda x: x[1],reverse=True)#sorts by second paramter, times it's in a level1
################################
            sorted(act_tups, key=lambda x: x[1])#sorts by second paramter, level1finds

            for atup in act_tups:
                activity=atup[0]
                l1selected=False
                #print"activity ",activity#to see if the break is working
                o_dict=possible_dicts.get(activity)#recall, this is the dict of kv pairs 1,2,3 and the level lists linked to the activity
                l1=o_dict.get(1)
                l15=o_dict.get(1.5)
                l2=o_dict.get(2)
                #
                # print len(l1)," level 1 os"
                # print len(l15)," level 15 os"
                # print len(l2)," level 2 os"
        ###########################################
                # for otup in o_tups:
                #     o=otup[0]
                #     print"o: ",o.start_time,o.end_time,o.interest#to see if the break is working
                #     if o in l1:
                #         #level1pairs[activity]=o#make the match
                #         prefix=prefix_base+"-%s-occurr-%s"%(str(activity.pk),str(o.pk))
                #         #print"prefix: ",prefix
                #         level1pairs[(activity,o)]=L1Check(prefix=prefix)
                #         #remove from everything
                #         o_tups.remove(otup)
                #         #resort
                #         sorted(o_tups, key=lambda x: x[1],reverse=True)#sorts by second paramter, times it's in a level1
                #         print"found an o/a kv pair"
                #         l1selected=True
                #         #print"about to breek in for o in li"
                #         break#stop going through os in l1 if you've found a match
                #     if l1selected:
                #         #print"about to breek in for o tup in o_tups"
                #         break#stop going through otups if you've found a match
                # if not l1selected:
                #     print"runningl2"
                #     l2=o_dict.get(2)#if still here bc no l1 found
                #     #this is where I'd like to choose a level2 of there's only 1 option,
                #     #but I'd have to have removed o levels in every dict all this tim for that to work
                #     #so this is on hold.
        # ############################

#######new try, making the o choice random #########
                if len(l1)>0:
                    #print "len l1: ",len(l1)
                    while len(l1)>0 and not l1selected:
                        o=choice(l1)
                        #print"o: ",o.start_time,o.end_time,o.interest#to see if the break is working
                        if o not in taken_os:
                            #print"not in taken"
                            prefix=prefix_base+"-%s-occurr-%s"%(str(activity.pk),str(o.pk))
                            #print"prefix: ",prefix
                            level1pairs[(activity,o,"Perfect Match")]=L1Check(prefix=prefix)
                            taken_os.append(o)
                            l1.remove(o)
                            l1selected=True
                            break
                        else:
                            #print "o taken, keep going"
                            l1.remove(o)

                elif len(l15)>0:
                    #print "len l15: ",len(l15)
                    while len(l15)>0 and not l1selected:
                        o=choice(l15)
                        #print"o: ",o.start_time,o.end_time,o.interest#to see if the break is working
                        if o not in taken_os:
                            #print"not in taken"
                            prefix=prefix_base+"-%s-occurr-%s"%(str(activity.pk),str(o.pk))
                            #print"prefix: ",prefix
                            level1pairs[(activity,o,"+/- Interest but no Conflicts")]=L1Check(prefix=prefix)
                            taken_os.append(o)
                            l15.remove(o)
                            l1selected=True
                            break
                        else:
                            #print "o taken, keep going"
                            l15.remove(o)

                elif len(l2)>0:
                    #print "len l2: ",len(l2)
                    while len(l2)>0 and not l1selected:
                        o=choice(l2)
                        #print"o: ",o.start_time,o.end_time,o.interest#to see if the break is working
                        if o not in taken_os:
                            #print"not in taken"
                            prefix=prefix_base+"-%s-occurr-%s"%(str(activity.pk),str(o.pk))
                            #print"prefix: ",prefix
                            level1pairs[(activity,o,"+/- Interest and Player Conflicts")]=L1Check(prefix=prefix)
                            taken_os.append(o)
                            l2.remove(o)
                            l1selected=True
                            break
                        else:
                            #print "o taken, keep going"
                            l2.remove(o)

###############end random experiment

            new_context={"added2schedule":added2schedule,"save_attempt":save_attempt,"save_success":save_success,"level1pairs":level1pairs,"slotcreateform":SlotCreate(),"activities":activities,"con":con,"con_list":Con.objects.all()}
            extra_context.update(new_context)
            return render(request, template, extra_context)
        else:
            if 'save schedule' in request.POST:
                save_attempt=True
                for k in post_keys:
                    lsplit=k.split("-")
                    #print "lsplit ",lsplit
                    if len(lsplit)==5 and lsplit[4]=='add2sched':
                        o=Occurrence.objects.get(pk=int(lsplit[3]))
                        if lsplit[0]=="challenge":
                            a=Challenge.objects.get(pk=int(lsplit[1]))
                            o.challenge=a
                        elif lsplit[0]=="training":
                            a=Training.objects.get(pk=int(lsplit[1]))
                            o.training=a
    #############################
                        o.save() #hold on, both to check if is okay
        ###############################
                        added2schedule.append(o)
                        save_success=True
    #if not post, or just saves
    for q in [Challenge.objects.filter(con=con, RCaccepted=True),Training.objects.filter(con=con, RCaccepted=True)]:
        cycle+=1
        temp_dict={}
        for obj in q:
            if (obj.is_a_training() and obj.sessions and len(obj.occurrence_set.all())<obj.sessions) or (len(obj.occurrence_set.all())<=0):
            #if len(obj.occurrence_set.all())<=0:#later will have to be different, for repeat trainings
                score=len(obj.get_figurehead_blackouts())
                if score not in temp_dict:
                    temp_dict[score]=[obj]
                else:
                    this_list=temp_dict.get(score)
                    this_list.append(obj)
                    temp_dict[score]=list(this_list)

        score_list=temp_dict.keys()
        score_list.sort(reverse=True)
        od_list=[]
        for score in score_list:
            temp_list=temp_dict.get(score)
            for act in temp_list:
                od  = collections.OrderedDict()
                od["act"]=act
                od["score"]=score
                od["check_form"]=ActCheck(prefix=(act_types[cycle]+"-"+str(act.pk)))
                od_list.append(od)
        activities.append(od_list)


    new_context={"added2schedule":added2schedule,"save_attempt":save_attempt,"save_success":save_success,"level1pairs":level1pairs,"slotcreateform":SlotCreate(),"activities":activities,"con":con,"con_list":Con.objects.all()}
    extra_context.update(new_context)
    return render(request, template, extra_context)

#-------------------------------------------------------------------------------

@login_required
def act_sched(
    request,
    template='swingtime/act_sched.html',
    con_id=None,
    **extra_context
):
    if con_id:
        con=Con.objects.get(pk=con_id)
    else:
        con=Con.objects.most_upcoming()

    challenges=Occurrence.objects.filter(challenge__con=con)
    trainings=Occurrence.objects.filter(training__con=con)

    new_context={"activities":[challenges,trainings],"con":con,"con_list":Con.objects.all()}
    extra_context.update(new_context)
    return render(request, template, extra_context)

#-------------------------------------------------------------------------------
@login_required
def sched_status(
    request,
    template='swingtime/sched_status.html',
    con_id=None,
    form_class=ConSchedStatusForm,
    save_success=False
):
    if con_id:
        con = get_object_or_404(Con, pk=con_id)
    else:
        con = get_object_or_404(Con, pk=Con.objects.most_upcoming().pk)

    if request.method == 'POST':
        form = form_class(request.POST, instance=con)
        if form.is_valid():
            form.save()
            save_success=True
            return render(request, template, {'save_success':save_success,'con':con, 'con_list':Con.objects.all(),'form': form})

    else:
        form = form_class(instance=con)

    return render(request, template, {'save_success':save_success,'con':con,'con_list':Con.objects.all(),'form': form})

#-------------------------------------------------------------------------------
@login_required
def sched_assist_tr(
    request,
    act_id,
    template='swingtime/sched_assist.html',
    makedummies=False
):
    start=datetime.now()
    try:
        act=Training.objects.get(pk=act_id)
    except:
        return render(request, template, {})

    if "level" in request.GET:
        level=int(request.GET['level'])
    else:
        level=1

    if request.method == 'POST':
        if 'save_activity' in request.POST:
            form=TInterestForm(request.POST,instance=act)
            if form.is_valid():
                form.save()
        elif "makedummies" in request.POST:
            form=TInterestForm(instance=act)
            makedummies=True
    else:
        form=TInterestForm(instance=act)

    start=datetime.now()
    slots= act.sched_conflict_score(level=level,makedummies=makedummies)
    elapsed=datetime.now()-start
    print "all done!!! Took %s (%s Seconds)"% (elapsed,elapsed.seconds)

    return render(request, template, {'level':level,'form':form,'act':act,'slots':slots,"training":act,'challenge':None})

#-------------------------------------------------------------------------------
@login_required
def sched_assist_ch(
    request,
    act_id,
    template='swingtime/sched_assist.html',
    makedummies=False
):

    try:
        act=Challenge.objects.get(pk=act_id)
    except:
        return render(request, template, {})
    if "level" in request.GET:
        level=int(request.GET['level'])
    else:
        level=1

    if request.method == 'POST':
        if 'save_activity' in request.POST:
            form=CInterestForm(request.POST,instance=act)
            if form.is_valid():
                form.save()
        elif "makedummies" in request.POST:
            makedummies=True
            form=CInterestForm(instance=act)
    else:
        form=CInterestForm(instance=act)

    start=datetime.now()
    slots=act.sched_conflict_score(level=level,makedummies=makedummies)#make second so change in actiity changed slots
    elapsed=datetime.now()-start
    return render(request, template, {'level':level,'form':form,'act':act,'slots':slots,"training":None,'challenge':act})

#-------------------------------------------------------------------------------
@login_required
def calendar_home(
    request,
    template='calendar_home.html',
    **extra_context
):

    return render(request, template, extra_context)

#-------------------------------------------------------------------------------
# @login_required
# def event_listing(
#     request,
#     template='swingtime/event_list.html',
#     events=None,
#     **extra_context
# ):
#     '''
#     View all ``events``.
#
#     If ``events`` is a queryset, clone it. If ``None`` default to all ``Event``s.
#
#     Context parameters:
#
#     ``events``
#         an iterable of ``Event`` objects
#
#     ... plus all values passed in via **extra_context
#     '''
#     if events is None:
#         events = Event.objects.all()
#
#     extra_context['events'] = events
#     return render(request, template, extra_context)


#-------------------------------------------------------------------------------
# @login_required
# def event_view(
#     request,
#     pk,
#     template='swingtime/event_detail.html',
#     event_form_class=forms.EventForm,
#     recurrence_form_class=forms.MultipleOccurrenceForm,
#     save_success=False,
# ):
#     '''
#     View an ``Event`` instance and optionally update either the event or its
#     occurrences.
#
#     Context parameters:
#
#     ``event``
#         the event keyed by ``pk``
#
#     ``event_form``
#         a form object for updating the event
#
#     ``recurrence_form``
#         a form object for adding occurrences
#     '''
#     event = get_object_or_404(Event, pk=pk)
#     event_form = recurrence_form = None
#     if request.method == 'POST':
#         if '_update' in request.POST:
#             event_form = event_form_class(request.POST, instance=event)
#             if event_form.is_valid():
#                 event_form.save(event)
#                 save_success=True
#                 return http.HttpResponseRedirect(request.path)
#         elif '_add' in request.POST:
#             recurrence_form = recurrence_form_class(request.POST)
#             if recurrence_form.is_valid():
#                 recurrence_form.save(event)
#                 save_success=True
#                 return http.HttpResponseRedirect(request.path)
#         else:
#             return http.HttpResponseBadRequest('Bad Request')
#
#     data = {
#         'save_success':save_success,#probably doesn't run
#         'event': event,
#         'event_form': event_form or event_form_class(instance=event),
#         'recurrence_form': recurrence_form or recurrence_form_class(initial={'dtstart': datetime.now()})
#     }
#     return render(request, template, data)


#-------------------------------------------------------------------------------
@login_required
def occurrence_view(
    request,
    pk,
    template='swingtime/occurrence_detail.html',
    form_class=forms.SingleOccurrenceForm,
    save_success=False
):
    '''
    View a specific occurrence and optionally handle any updates.

    Context parameters:

    ``occurrence``
        the occurrence object keyed by ``pk``

    ``form``
        a form object for updating the occurrence
    '''
    occurrence = get_object_or_404(Occurrence, pk=pk)
    conflict_free=False
    conflict={}
    no_list=["",u'',None,"None"]
    get_dict={}
    if "training" in request.GET and request.GET['training'] not in no_list:
        training=Training.objects.get(pk=request.GET['training'])
        get_dict['training']=training
        #recurrence_dict['training']=training#fon't need this anymore, right?
    if "challenge" in request.GET and request.GET['challenge'] not in no_list:
        challenge=Challenge.objects.get(pk=request.GET['challenge'])
        get_dict['challenge']=challenge

    if request.method == 'POST':
        form = form_class(request.POST, instance=occurrence)
        if form.is_valid():
            if "update" in request.POST:
                form.save()
                save_success=True
                #return render(request, template, {'save_success':save_success,'occurrence': occurrence, 'form': form})
            elif "check" in request.POST:
                figurehead_conflict=occurrence.figurehead_conflict()
                if figurehead_conflict:
                    conflict["figurehead_conflict"]=figurehead_conflict
                participant_conflict=occurrence.participant_conflict()
                if participant_conflict:
                    conflict["participant_conflict"]=participant_conflict
                blackout_conflict=occurrence.blackout_conflict()
                if blackout_conflict:
                    conflict["blackout_conflict"]=blackout_conflict
                if len(conflict)<=0:
                    conflict_free=True
            elif "delete" in request.POST:
                if occurrence and occurrence.location:
                    lpk=int(occurrence.location.pk)#to keep after occurrence gets deleted
                    date=datetime.date(occurrence.start_time)
                    occurrence.delete()
                    return redirect('swingtime-daily-location-view',lpk,date.year,date.month,date.day)

    else:
        form = form_class(instance=occurrence,initial=get_dict)

    try:
        location=occurrence.location
    except:
        location=None

    return render(request, template, {'location':location,'conflict_free':conflict_free,'conflict':conflict,'save_success':save_success,'occurrence': occurrence, 'form': form})


#-------------------------------------------------------------------------------
@login_required
def add_event(
    request,
    template='swingtime/add_event.html',
    recurrence_form_class=forms.SingleOccurrenceForm,
):
    '''
    Add a new ``Event`` instance and 1 or more associated ``Occurrence``s.

    Context parameters:

    ``dtstart``
        a datetime.datetime object representing the GET request value if present,
        otherwise None

    ``event_form``
        a form object for updating the event

    ``recurrence_form``
        a form object for adding occurrences

    '''
    save_success=False
    dtstart = None
    drend=None
    training=None
    challenge=None
    location=None
    conflict={}
    conflict_free=False
    no_list=["",u'',None,"None"]
    recurrence_dict={}
    get_dict={}
    #########fetch all get values as intials##########
    if 'dtstart' in request.GET:
        try:
            dtend = dtstart = parser.parse(request.GET['dtstart'])
            get_dict["start_time"]=dtstart
            recurrence_dict["start_time"]=dtstart
            recurrence_dict["end_time"]=dtend#setting initial as same, chang elater d/t post info or model method
        except(TypeError, ValueError) as exc:
            # TODO: A badly formatted date is passed to add_event
            logging.warning(exc)
    if "location" in request.GET and request.GET['location'] not in no_list:
        location=Location.objects.get(pk=request.GET['location'])
        get_dict['location']=location
        recurrence_dict['location']=location
    if "training" in request.GET and request.GET['training'] not in no_list:
        training=Training.objects.get(pk=request.GET['training'])
        get_dict['training']=training
        recurrence_dict['training']=training
    if "challenge" in request.GET and request.GET['challenge'] not in no_list:
        challenge=Challenge.objects.get(pk=request.GET['challenge'])
        get_dict['challenge']=challenge
        recurrence_dict['challenge']=challenge
    #print "get dict",get_dict
    ########done fetching get values#########
    #initial offering, might get overwritten w/post
    recurrence_form = recurrence_form_class(initial=recurrence_dict)
    ##########################

    if request.method == 'POST':
        #selection = request.POST.copy()
        #print "selection", selection

        dtend_post=[u'end_time_1',u'end_time_0_year',u'end_time_0_month','end_time_0_day']
        if len( set(dtend_post).intersection(request.POST.keys())) > 0:
            dtend_str=request.POST['end_time_0_year']+"-"+request.POST['end_time_0_month']+"-"+request.POST['end_time_0_day']+"T"+request.POST['end_time_1']
            dtend=parser.parse(dtend_str)
            recurrence_dict['end_time']=dtend#I think this is unnecessary

        #these will override the train/chal set from get, if they're there.
        if "challenge" in request.POST and request.POST['challenge'] not in no_list:
            challenge=Challenge.objects.get(pk=request.POST['challenge'])
        if "training" in request.POST and request.POST['training'] not in no_list:
            training=Training.objects.get(pk=request.POST['training'])

        recurrence_form = recurrence_form_class(request.POST)

        if recurrence_form.is_valid():
            occurrence=recurrence_form.save(commit=False)

            if occurrence.end_time<=occurrence.start_time:
                occurrence.end_time=occurrence.get_endtime()
            recurrence_form = recurrence_form_class(instance=occurrence)#to keeo calculated end time if conflict

#this seems to not refresh conflict items, for some reason
            if ("check" in request.POST):#will this run if not saved yet?
                figurehead_conflict=occurrence.figurehead_conflict()
                if figurehead_conflict:
                    conflict["figurehead_conflict"]=figurehead_conflict
                participant_conflict=occurrence.participant_conflict()
                if participant_conflict:
                    conflict["participant_conflict"]=participant_conflict
                blackout_conflict=occurrence.blackout_conflict()
                if blackout_conflict:
                    conflict["blackout_conflict"]=blackout_conflict
                if len(conflict)<=0:
                    conflict_free=True

            if ("save" in request.POST):
                occurrence.save()
                save_success=True#this doesn't d anyhting, I'm not able to pass it on unless I change the url
                return redirect('swingtime-occurrence',occurrence.id)#important, otherwise can make new ones forever and think editing same one

    # #this happens regardless of post or not
    return render(request,template,
        {'conflict_free':conflict_free,'conflict':conflict,'save_success':save_success,'dtstart': dtstart, 'single_occurrence_form': recurrence_form})


#-------------------------------------------------------------------------------
@login_required
def _datetime_view(
    request,
    template,
    dt,
    loc_id=None,
    timeslot_factory=None,
    items=None,
    params=None
):
    '''
    Build a time slot grid representation for the given datetime ``dt``. See
    utils.create_timeslot_table documentation for items and params.

    Context parameters:

    ``day``
        the specified datetime value (dt)

    ``next_day``
        day + 1 day

    ``prev_day``
        day - 1 day

    ``timeslots``
        time slot grid of (time, cells) rows

    '''
    timeslot_factory = timeslot_factory or utils.create_timeslot_table
    params = params or {}

    try:
        con=Con.objects.get(start__lte=dt, end__gte=dt)
        all_locations=con.get_locations()
        if loc_id:
            locations=[Location.objects.get(pk=int(loc_id))]
        else:
            locations=con.get_locations()
    except ObjectDoesNotExist:
        con=None
        all_locations=[]
        locations=[]

    return render(request, template, {
        'day':       dt,
        'con':       con,
        'locations': locations,
        'loc_id':loc_id,
        'maxwidth': 99/(len(locations)+1),
        'next_day':  dt + timedelta(days=+1),
        'prev_day':  dt + timedelta(days=-1),
        'timeslots': timeslot_factory(dt=dt, items=items, loc_id=loc_id,**params)
    })


#-------------------------------------------------------------------------------
@login_required
def day_view(request, year, month, day, template='swingtime/daily_view.html', **params):
    '''
    See documentation for function``_datetime_view``.

    '''
    dt = datetime(int(year), int(month), int(day))
    return _datetime_view(request, template, dt, **params)


#-------------------------------------------------------------------------------
@login_required
def day_location_view(request, loc_id, year, month, day, template='swingtime/daily_view.html', **params):
    '''
    See documentation for function``_datetime_view``.

    '''
    dt = datetime(int(year), int(month), int(day))
    return _datetime_view(request, template, dt, loc_id, **params)

#-------------------------------------------------------------------------------
@login_required
def day_clone(request, con_id=None,template='swingtime/day_clone.html', **params):
    """This give soption to clone 1 day's Occurrence settings to another.
    It will not overwrite anything that already exists, only if time is available.
    Makes empty occurrences, does not move chal/train over, but does retain interest"""
    save_attempt=False
    #save_succes=False
    save_succes=[]

    if con_id:
        try:
            con=Con.objects.get(pk=con_id)
        except:
            return render(request,template, {})
    else:
        con=Con.objects.most_upcoming()

    form=DLCloneForm(request.POST or None,date_list=con.get_date_range(), loc_list=con.get_locations())

    if request.method == 'POST':#there's only one post option
        save_attempt=True
        fromdate=parse(request.POST['fromdate']).date()
        from_start=fromdate
        from_end=(fromdate + timedelta(days=+1))
        fromlocation=Location.objects.get(pk=request.POST['fromlocation'])
        todate=parse(request.POST['todate']).date()
        tolocation=Location.objects.get(pk=request.POST['tolocation'])

        sample_slots=Occurrence.objects.filter(start_time__gte=fromdate, end_time__lt=from_end, location=fromlocation)

        for s in sample_slots:
            target_start=datetime(year=todate.year, month=todate.month, day=todate.day, hour=s.start_time.hour,minute=s.start_time.minute)
            target_end=datetime(year=todate.year, month=todate.month, day=todate.day, hour=s.end_time.hour ,minute=s.end_time.minute)
            if tolocation.is_free(target_start,target_end):
                clone=Occurrence(start_time=target_start,end_time=target_end,interest=s.interest,location=tolocation)
                save_succes.append(clone)
                clone.save()
        return render(request,template,{'todate':todate,'tolocation':tolocation,'save_succes':save_succes,'save_attempt':save_attempt,'form':form})

    #only runs if not post
    return render(request,template,{'save_succes':save_succes,'save_attempt':save_attempt,'form':form})


#-------------------------------------------------------------------------------

@login_required
def today_view(request, template='swingtime/daily_view.html', **params):
    '''
    See documentation for function``_datetime_view``.

    '''
    return _datetime_view(request, template, datetime.now(), **params)


#-------------------------------------------------------------------------------
@login_required
def year_view(request, year, template='swingtime/yearly_view.html', queryset=None):
    '''

    Context parameters:

    ``year``
        an integer value for the year in questin

    ``next_year``
        year + 1

    ``last_year``
        year - 1

    ``by_month``
        a sorted list of (month, occurrences) tuples where month is a
        datetime.datetime object for the first day of a month and occurrences
        is a (potentially empty) list of values for that month. Only months
        which have at least 1 occurrence is represented in the list

    '''
    year = int(year)
    queryset = queryset._clone() if queryset is not None else Occurrence.objects.select_related()
    occurrences = queryset.filter(
        models.Q(start_time__year=year) |
        models.Q(end_time__year=year)
    )

    def group_key(o):
        return datetime(
            year,
            o.start_time.month if o.start_time.year == year else o.end_time.month,
            1
        )

    return render(request, template, {
        'year': year,
        'by_month': [(dt, list(o)) for dt,o in itertools.groupby(occurrences, group_key)],
        'next_year': year + 1,
        'last_year': year - 1

    })


#-------------------------------------------------------------------------------
@login_required
def month_view(
    request,
    year,
    month,
    template='swingtime/monthly_view.html',
    queryset=None
):
    '''
    Render a tradional calendar grid view with temporal navigation variables.

    Context parameters:

    ``today``
        the current datetime.datetime value

    ``calendar``
        a list of rows containing (day, items) cells, where day is the day of
        the month integer and items is a (potentially empty) list of occurrence
        for the day

    ``this_month``
        a datetime.datetime representing the first day of the month

    ``next_month``
        this_month + 1 month

    ``last_month``
        this_month - 1 month

    '''
    year, month = int(year), int(month)
    cal         = calendar.monthcalendar(year, month)
    dtstart     = datetime(year, month, 1)
    last_day    = max(cal[-1])
    dtend       = datetime(year, month, last_day)

    # TODO Whether to include those occurrences that started in the previous
    # month but end in this month?
    queryset = queryset._clone() if queryset is not None else Occurrence.objects.select_related()
    occurrences = queryset.filter(start_time__year=year, start_time__month=month)

    def start_day(o):
        return o.start_time.day

    by_day = dict([(dt, list(o)) for dt,o in itertools.groupby(occurrences, start_day)])
    data = {
        'today':      datetime.now(),
        'calendar':   [[(d, by_day.get(d, [])) for d in row] for row in cal],
        'this_month': dtstart,
        'next_month': dtstart + timedelta(days=+last_day),
        'last_month': dtstart + timedelta(days=-1),
    }

    return render(request, template, data)
