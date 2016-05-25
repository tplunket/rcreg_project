from django.conf.urls import url
from swingtime import views
from django.views.generic import TemplateView

urlpatterns = [
#______________Dahmer custom URLS/Views, so templates can live together___________________
    url(r'^submitted/challenges/con/(?P<con_id>\d+)/$', 'swingtime.views.chal_submit',name='chal_submit'),
    url(r'^submitted/challenges/$', 'swingtime.views.chal_submit',name='chal_submit'),
    url(r'^accepted/challenges/con/(?P<con_id>\d+)/$', 'swingtime.views.chal_accept',name='chal_accept'),
    url(r'^accepted/challenges/$', 'swingtime.views.chal_accept',name='chal_accept'),
    url(r'^rejected/challenges/con/(?P<con_id>\d+)/$', 'swingtime.views.chal_reject',name='chal_reject'),
    url(r'^rejected/challenges/$', 'swingtime.views.chal_reject',name='chal_reject'),

    url(r'^submitted/trainings/con/(?P<con_id>\d+)/$', 'swingtime.views.train_submit',name='train_submit'),
    url(r'^submitted/trainings/$', 'swingtime.views.train_submit',name='train_submit'),
    url(r'^accepted/trainings/con/(?P<con_id>\d+)/$', 'swingtime.views.train_accept',name='train_accept'),
    url(r'^accepted/trainings/$', 'swingtime.views.train_accept',name='train_accept'),
    url(r'^rejected/trainings/con/(?P<con_id>\d+)/$', 'swingtime.views.train_reject',name='train_reject'),
    url(r'^rejected/trainings/$', 'swingtime.views.train_reject',name='train_reject'),

    url(r'^scheduled/con/(?P<con_id>\d+)/$', 'swingtime.views.act_sched',name='act_sched'),
    url(r'^scheduled/$', 'swingtime.views.act_sched',name='act_sched'),
    url(r'^unscheduled/con/(?P<con_id>\d+)/$', 'swingtime.views.act_unsched',name='act_unsched'),
    url(r'^unscheduled/$', 'swingtime.views.act_unsched',name='act_unsched'),

    url(r'^schedule/status/con/(?P<con_id>\d+)/$', 'swingtime.views.sched_status',name='sched_status'),
    url(r'^schedule/status/$', 'swingtime.views.sched_status',name='sched_status'),

    url(r'^schedule/assistance/training/(?P<act_id>\d+)/$', 'swingtime.views.sched_assist_tr',name='sched_assist_tr'),
    url(r'^schedule/assistance/challenge/(?P<act_id>\d+)/$', 'swingtime.views.sched_assist_ch',name='sched_assist_ch'),

    url(r'^calendar/location/(?P<loc_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$','swingtime.views.day_location_view',name='swingtime-daily-location-view'),
    url(r'^calendar/day_clone(?:/(?P<con_id>\d+))?/$', 'swingtime.views.day_clone',name='day_clone'),#can take con arguments, but I ahven'y written convenent links for that
    #cool regex to say con_id may or may not be present:http://stackoverflow.com/questions/2325433/making-a-regex-django-url-token-optional
    url(r'^calendar/location/(?P<loc_id>\d+)(?:/con/(?P<con_id>\d+))?/$',views.location_view,name='swingtime-location-view'),


#________________________end my custom URLS____________________________________
    url(
        r'^calendar/home/$',
        views.calendar_home,
        name='calendar_home'
    ),

    url(
        r'^(?:calendar/)?$',
        views.today_view,
        name='swingtime-today'
    ),

    url(
        r'^calendar/(?P<year>\d{4})/$',
        views.year_view,
        name='swingtime-yearly-view'
    ),

    url(
        r'^calendar/(\d{4})/(0?[1-9]|1[012])/$',
        views.month_view,
        name='swingtime-monthly-view'
    ),

    url(
        r'^calendar/(\d{4})/(0?[1-9]|1[012])/([0-3]?\d)/$',
        views.day_view,
        name='swingtime-daily-view'
    ),

    # url(
    #     r'^events/$',
    #     views.event_listing,
    #     name='swingtime-events'
    # ),
##################i use this one all the time, need to rewrite w/out events
    url(
        r'^events/add/$',
        views.add_event,
        name='swingtime-add-event'
    ),
####################################################

    # url(
    #     r'^events/(\d+)/$',
    #     views.event_view,
    #     name='swingtime-event'
    # ),

    url(
        #r'^events/(\d+)/(\d+)/$',
        r'^occurrence/(\d+)/$',
        views.occurrence_view,
        name='swingtime-occurrence'
    ),
]
