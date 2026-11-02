
# tactiq.io free youtube transcript

# Conditional Orders with Interactive Brokers API using IB-Insync in Python

# https://www.youtube.com/watch/XgUE0fhIfh0

00:00:01.319 hey guys so this video I'm going to be
00:00:02.840 talking about conditional orders so
00:00:05.080 conditional orders are orders that only
00:00:06.879 trigger if some condition is true so for
00:00:10.480 example it could be a price condition
00:00:12.120 like let's say um only buy Tesla when
00:00:15.240 Nvidia is under
00:00:17.320 $500 or um similarly it can be a
00:00:20.160 percentage change condition like only by
00:00:22.960 Tesla if Nvidia is uh down 3% or more um
00:00:28.359 or it can a better example might be only
00:00:31.720 sell a Tesla call if you're doing
00:00:33.520 covered calls if Tesla is um up 2% or
00:00:37.960 more because you want to get that
00:00:40.280 premium and if Tesla's up 2% the call
00:00:43.480 you're selling has a higher price so
00:00:46.160 those are a few examples of uh uh
00:00:48.559 conditional orders there could also be
00:00:50.399 time based conditional orders like only
00:00:53.039 buy Tesla if it's before 12:00 p.m. or
00:00:56.840 only uh sell only buy Tesla if it's um
00:01:01.280 after uh 300
00:01:05.438 p.m. okay so um there's also a volume
00:01:09.360 condition say like only buy Tesla when
00:01:11.920 some stock like nvidia's volume is under
00:01:15.360 um a million dollars or something like
00:01:17.520 that so there's so as you see in the
00:01:20.159 source code and um uh in order. py
00:01:24.000 there's these um order condition things
00:01:26.720 and there's price condition time
00:01:28.400 condition margin condition
00:01:30.759 execution condition volume condition and
00:01:32.720 percent change condition of course this
00:01:34.560 is with IB in sync um one more thing
00:01:37.880 maybe we should specify I'm not going to
00:01:39.360 go over in this video we can make
00:01:41.399 another video on margin condition but
00:01:43.920 margin condition is like let's say if
00:01:45.600 you're margin um percentage is below
00:01:49.680 something uh you can execute a trade or
00:01:52.600 or it has to be above something to
00:01:54.520 execute a trade there's also an
00:01:56.320 execution condition which I'm not really
00:01:58.719 familiar with I've never used used that
00:02:00.200 before but if you Google uh twws API
00:02:04.640 conditional orders you might get more
00:02:06.600 information on on this um I guess it
00:02:10.840 doesn't say that much but like um uh an
00:02:14.280 execution conditions anyways another
00:02:17.480 quick thing is there's a conjunction
00:02:19.440 thing is you can combine um uh orders
00:02:23.440 like making it and or that sort of thing
00:02:26.200 so uh let's get started and show a few
00:02:28.840 examples okay
00:02:30.319 so first of course we connect to IB as
00:02:33.200 always
00:02:36.160 um from IB in sync import Star IB equals
00:02:41.360 IB ib.
00:02:43.599 connect for equals
00:02:47.959 401 uh you know what let's make Port 404
00:02:51.519 let's make client
00:02:52.879 ID equal zero okay did I connect to
00:02:57.640 IB oh sorry it's good I made this
00:03:00.800 mistake you tell that sly because um you
00:03:03.560 need that for the J
00:03:05.760 notebook okay oops cuz it already
00:03:09.720 connected but the the asyncio is messed
00:03:12.280 up
00:03:13.799 okay now we connected to I okay so let's
00:03:17.319 first start with a Time based order and
00:03:20.239 you know what let me let me just uh go
00:03:22.599 back one second and show you guys when
00:03:25.400 you go on Ivy Gateway you have to know
00:03:28.159 which time zone your IB Gateway is so
00:03:31.080 like I'm opening a new IB
00:03:33.720 Gateway and Below there's a thing called
00:03:36.200 more options and uh it's it'll give you
00:03:39.560 a time
00:03:41.159 zone make sure you have the right time
00:03:43.599 zone I put mine as America New York I
00:03:46.439 don't live there but that's what I put
00:03:48.599 it as um but I accidentally had
00:03:51.519 California and uh this led to me getting
00:03:54.720 things completely wrong so make sure you
00:03:57.400 have you you have the time on set I
00:04:00.239 recommend using eastern time because
00:04:01.760 that's when the Market opens so if so
00:04:04.360 yeah so if you need to make sure you
00:04:06.439 have this time zone that you're familiar
00:04:08.640 with um okay so now time based order so
00:04:11.920 let's Show an example of how this is
00:04:13.480 done so um let's Okay Let's do let's
00:04:18.199 just uh first of all Let's uh let's
00:04:21.199 first start with examples with stock uh
00:04:24.040 and stocks and then we can do a few
00:04:26.320 option examples so like let's say this
00:04:28.479 is uh contract we want to trade trade
00:04:33.759 and let's make this Tesla we can make it
00:04:36.800 um
00:04:38.600 Tesla equals
00:04:41.039 stock
00:04:42.720 symbol equals
00:04:45.680 Tesla currency equals
00:04:51.400 USD equals
00:04:57.080 smart Okay do I be that qualified
00:05:00.360 contracts
00:05:01.600 Tesla okay so now we'll have the other
00:05:05.560 contract uh later we you know what I'll
00:05:08.199 talk about this later okay just for now
00:05:10.520 this is just the contract you want to
00:05:11.759 trade which is Tesla
00:05:14.280 so let's Show an example of sorry I'm
00:05:18.000 sick I thought I I would get through
00:05:20.520 this video without coughing but anyways
00:05:23.319 let's Show an example of the time based
00:05:25.280 order so how do we do a Time based order
00:05:27.919 so let's first create a regular order
00:05:30.240 and this is to buy Tesla at 220 and note
00:05:34.840 unfortunately Tesla is below 220 this
00:05:37.919 will trigger now actually um yeah let's
00:05:41.759 uh get Market data for Tesla we'll do um
00:05:45.560 Tesla ticker equals
00:05:49.240 ib. Market
00:05:51.720 data uh Tesla this FAL F and then if I
00:05:58.080 do a Tesla ticker
00:06:01.440 do uh market price I'll see that oh s oh
00:06:06.560 San because it didn't fill yet um
00:06:09.759 sometimes you should do like a ib. sleep
00:06:12.960 to or whatever to make sure it fills
00:06:15.919 okay so as you see the market price is
00:06:17.520 like
00:06:19.560 this weak anyway so this should fill
00:06:22.639 right away because Tesla is um under 220
00:06:27.280 and we have a limit for 220 but I can do
00:06:30.599 this thing called a Time condition I can
00:06:32.240 do time uh
00:06:35.639 condition equals time
00:06:38.560 condition and then I can do time
00:06:41.360 condition do time this is the time and
00:06:45.240 then I set a time so let's say I'm I
00:06:48.919 I'll make a time up like let's say today
00:06:50.639 is the 16th and I'm going to say like
00:06:53.360 the order will only be valid after now
00:06:55.759 it's 12:06 Eastern let's say the order
00:06:59.039 will only only be valid after um 1208
00:07:02.840 Eastern so in 2 minutes okay so um this
00:07:06.759 is the time oh sorry there's like a Time
00:07:10.120 condition that um is
00:07:13.440 more and this could be true or
00:07:16.120 false um and is more means that it's
00:07:19.599 after is if it's true if it's false it
00:07:23.919 means it's before and what you do is you
00:07:27.280 append the conditions you set the order
00:07:29.960 conditions um you it's a list by default
00:07:33.800 of empty list you do append and you
00:07:35.879 append this time condition okay so now
00:07:38.199 let me show you how you can place order
00:07:39.680 you can do trade equals ib. place order
00:07:43.479 oh oops sorry I called it uh Tesla order
00:07:47.759 and look at the order status at first
00:07:49.360 it's pending submit then it's um
00:07:53.720 pre-submitted because although it should
00:07:56.159 fill because Tesla's under 220 in fact
00:07:58.919 un forun now it's 218 man the nightmare
00:08:02.000 with Tesla never ends um uh yeah this
00:08:06.759 couldn't get ugly fast the Tesla Oh see
00:08:10.199 it made it to 08 and it filled so it was
00:08:13.039 pre-submitted until 08 and then it
00:08:15.080 filled okay so just to show you like so
00:08:18.840 if I were to do it again do 210 it'll
00:08:21.520 stay at presubmit
00:08:23.400 always until you get the 210 okay so
00:08:26.680 this is an example of a Time based
00:08:28.479 condition right
00:08:29.800 so now let's uh give you an example of
00:08:32.279 of a um price condition uh so first
00:08:35.799 let's cancel all the orders we can do
00:08:37.839 four
00:08:39.559 order oops order in ib. open
00:08:45.440 orders I'm canceling all the orders that
00:08:47.880 are open cancel order
00:08:52.880 order so let me okay so uh and we can
00:08:57.640 check uh that we canel order order
00:08:59.680 orders we do IB that open
00:09:02.260 [Music]
00:09:06.839 orders
00:09:09.160 uh oh sorry I be that open orders yeah
00:09:13.880 we canceled it so now let me show you an
00:09:16.040 example of a price condition so this is
00:09:18.240 a condition based on like a different
00:09:20.240 contract or the same contract and you
00:09:23.320 have a price condition so let's let's
00:09:25.519 use for our example let's use Nvidia as
00:09:27.880 the other contract so Nidia equals stock
00:09:32.720 symbol equals uh
00:09:35.880 Nvidia uh exchange equals
00:09:40.000 smart currency equals USD and for this
00:09:43.600 one it actually is really important to
00:09:45.160 do ib. qualifying contracts Nvidia
00:09:48.240 because you're going to need this Con ID
00:09:50.760 thing for this thing so now let's define
00:09:53.680 the price condition as um as price
00:09:58.120 condition it's condition by the way you
00:10:01.839 don't have to do uh this thing empty and
00:10:04.600 then dot all the time you can just uh
00:10:07.320 put it in the argument so let's do it in
00:10:09.920 the argument for this one price
00:10:11.880 condition and then do
00:10:13.480 con
00:10:15.480 um H uh there's a con type thing I
00:10:19.440 wonder what the default is for that um
00:10:22.519 so
00:10:24.079 uh cont four oh sorry con type just
00:10:28.480 gives you like what type of condition
00:10:29.880 you have so um that's that's useless so
00:10:34.640 con ID equals Nvidia thaton
00:10:38.480 ID
00:10:40.040 um exchange equals um smart I don't know
00:10:45.360 if you need that um is more equals false
00:10:49.639 let's make it um if Nvidia is
00:10:52.920 um uh is under a certain amount we'll
00:10:56.200 buy it let's just just for a second
00:10:58.160 let's see what's nid price Nvidia
00:11:01.240 ticker equals IB direct Market
00:11:06.160 data data
00:11:09.800 Nidia b
00:11:14.079 b i. sleep too to give it time to fill
00:11:18.399 let's do Nvidia ticker do market
00:11:24.320 price so video is at
00:11:29.320 so let's make the condition that Nvidia
00:11:32.760 will be under
00:11:39.720 562.org
00:11:41.680 so this will only trigger if Nvidia is
00:11:44.160 under
00:11:58.959 here's this like conjunction thing um so
00:12:02.800 um uh you can make it like a and or an
00:12:05.279 or I'll show you guys in a second so
00:12:07.440 wait Nvidia is
00:12:21.320 562.org
00:12:24.360 um so let's make the order the same
00:12:27.120 thing so um
00:12:30.040 what's Tesla's price now thicker that
00:12:33.399 market price I want it to be executable
00:12:35.880 immediately so Tesla's definitely under
00:12:38.040 220 so this is an order and you have
00:12:40.959 your price
00:12:42.199 condition and um uh well nvidia's never
00:12:47.120 goes down so let's make this actually
00:12:50.560 563 .1 okay so it only will trigger if
00:12:56.160 Nvidia is under
00:12:57.639 563 uh price keeps changing I want to
00:13:00.639 show you guys example fast so let's
00:13:03.279 let's let's still make it 56.8 okay okay
00:13:08.399 so uh
00:13:11.399 sorry um so let's do a trade
00:13:15.440 equals ib. placeorder uh contract is
00:13:19.240 Tesla
00:13:20.760 here and um it's pending submit at first
00:13:25.800 and then it's pre-submitted why is
00:13:30.079 pre-submitted because Nvidia is above
00:13:52.550 [Music]
00:13:58.839 going to fill but as you see it doesn't
00:14:01.320 fill because Nvidia is um is above this
00:14:05.959 price by the you know what I'll make a
00:14:08.399 different example I'll do like is more
00:14:09.880 is true and then this should fill right
00:14:12.360 away because Nvidia is above
00:14:15.800 that so presubmit it at first and then
00:14:18.519 it gets to fill
00:14:21.040 okay hope that makes sense so there's
00:14:24.199 something similar called like a a
00:14:26.560 percent uh percent change
00:14:30.959 condition um percent change
00:14:34.920 condition so let's
00:14:37.480 use the same uh running example with the
00:14:40.959 order ORD is like
00:14:43.360 this and then um we can do a percent
00:14:46.959 change condition so we can do something
00:14:49.560 like uh like uh percent
00:14:53.600 uh
00:14:55.279 percent change sorry change change
00:14:59.399 condition
00:15:00.959 equals percent change condition change
00:15:05.160 percent equals um so let's look at
00:15:09.160 Nvidia and let's see what's what's the
00:15:11.120 deal with Nvidia today Nvidia ticker do
00:15:14.519 uh close minus Nvidia ticker do
00:15:19.000 um uh close is yesterday's price so we
00:15:21.759 want to know the percent
00:15:23.560 change um tier. last is the last is the
00:15:27.800 last trade price
00:15:30.399 um this minus that over the close should
00:15:33.639 be the percent
00:15:36.720 change it's about 3% well so let's do uh
00:15:42.279 percent changes uh
00:15:45.000 0 uh
00:15:46.959 035 03 03 4 so like this will not hit
00:15:52.120 because it's above that con ID equals
00:15:54.800 Nvidia that uh con ID that's important
00:15:59.160 um let's try this without writing
00:16:00.680 exchange equals smart I wonder if it if
00:16:03.000 it will work I think you you do have to
00:16:05.920 write exchange I think because you have
00:16:07.440 to look at Nvidia so and I think you do
00:16:10.519 have to write exchange plus smart um is
00:16:13.279 more let's make it
00:16:15.120 true and um again to add this condition
00:16:18.959 we're going to do the
00:16:22.000 order order.
00:16:24.639 conditions.
00:16:26.360 append percent change condition
00:16:32.800 uh but this is the actual Perc change
00:16:35.240 but so let's now place the order and
00:16:37.560 check the order status so we wanted a
00:16:40.680 point 3.4% for it to
00:16:44.160 work um so oh sorry I keep making the
00:16:47.560 same uh cut and paste error so at first
00:16:51.160 it's pending submit then it's going to
00:16:53.360 be stuck at pre-submitted
00:16:56.880 submitted filled
00:16:59.240 why is it
00:17:00.920 filled
00:17:12.520 um uh maybe maybe the way they calculate
00:17:15.480 the percent change is different than
00:17:17.640 what I what I was
00:17:19.400 thinking
00:17:21.000 um so wait let's just try 4% it's
00:17:24.199 definitely not
00:17:25.720 4% so um order status prese submitted
00:17:29.919 fil
00:17:32.120 um is a percent like this a full percent
00:17:36.919 so now it's presubmit
00:17:38.480 presubmit it stuck at presubmit it okay
00:17:41.760 so maybe it's like this now let's say we
00:17:43.760 do
00:17:44.679 3% pres submitted filled okay so this is
00:17:48.799 key I didn't even know this um uh
00:17:51.440 percent change needs to be the actual
00:17:55.520 number not the decimal wow they get you
00:17:59.200 with that so um this is the percent
00:18:01.320 change condition okay so there's also
00:18:04.039 like a volume
00:18:05.679 condition in
00:18:08.039 condition and this is like um basically
00:18:13.240 um we uh similarly we have the same
00:18:18.280 order and now we just have a volume
00:18:24.320 condition volume
00:18:27.320 condition
00:18:30.880 Eon ID equals Eon ID um exchange equals
00:18:36.400 smart is more uh let's make is more as
00:18:40.720 true um and uh we give the volume
00:18:44.360 threshold so by the way you can from the
00:18:47.200 ticker you can do Nvidia tier. volume to
00:18:50.600 get the volume but this is volume um and
00:18:54.679 it's like 100 times what it should be so
00:18:57.480 you actually need to multiply this by
00:18:59.400 100 I don't know why they do it this way
00:19:01.520 it's really weird but this is the actual
00:19:04.159 number so let's use uh let's say we wait
00:19:07.280 for 273 uh okay so let's make wait for
00:19:12.320 uh
00:19:13.880 273 yeah let's do that so we'll make
00:19:16.400 volume is
00:19:18.480 273 um so now let's add the volume
00:19:22.480 condition so of course we're going to
00:19:25.520 do. conditions. um append and volume
00:19:30.919 condition and then uh we'll we'll test
00:19:34.159 to see if it works we're going to do
00:19:36.080 like previously we're going to do trade
00:19:38.480 equals ib. place order order status
00:19:42.159 uh
00:19:44.240 um I guess it doesn't want the format
00:19:47.200 like this it like this so pending submit
00:19:50.400 always at
00:19:51.600 first uh then presubmit it and it's
00:19:54.919 stuck on presubmit because the volume
00:19:56.640 hasn't reached 27 735
00:19:59.799 something um but if we
00:20:03.679 wait should reach it eventually um let's
00:20:07.440 make this uh one like this so um order
00:20:12.039 set is preed by the way I found that if
00:20:14.799 you later like adjust the conditions and
00:20:18.360 then replace the order sometimes it
00:20:19.880 doesn't work so be careful when
00:20:22.679 modifying uh the
00:20:24.960 order um with conditions uh your better
00:20:28.360 off canceling the order and resubmitting
00:20:29.840 from my
00:20:31.520 experience anyways the order status now
00:20:33.760 is filled why because the volume has
00:20:37.080 gone above this so this is the volume
00:20:41.520 condition okay but like in reality um
00:20:45.600 we're not going to want to just like
00:20:47.120 have this like random limit price we're
00:20:49.559 going to want the like limit price to be
00:20:51.559 something like something that's
00:20:54.480 um uh something that's like uh we
00:20:57.720 compute right so let's assume that like
00:21:00.400 okay when our price condition holds
00:21:01.960 let's say um when Nvidia crashes or
00:21:06.080 whatever if Nidia goes down or whatever
00:21:08.960 um we want to um Place uh price at the
00:21:12.480 um midpoint so we can do something like
00:21:15.159 this um I think I'm going to need num
00:21:17.240 for this n p so let's define um first of
00:21:23.039 all let's define the order itself we're
00:21:24.720 going to do order equals limit order and
00:21:28.200 then uh we're going to make a buy order
00:21:30.600 so the goal here is not to just blindly
00:21:32.600 buy at 220 but to buy at something like
00:21:35.159 let's say midpoint - 10 cents so um this
00:21:39.360 is going to be a dynamic it's going to
00:21:40.840 continuously change um when the as the
00:21:43.760 price of the ticker changes so so uh
00:21:46.760 we're going to buy let's say one share
00:21:49.200 and the limit price let's start it at
00:21:51.200 like really small number like like 1
00:21:53.880 cent um just because um it's not not
00:21:58.200 going to hit at first okay and then let
00:22:01.039 me show you guys so uh uh we can do um
00:22:05.000 remember we had the Tesla ticker but we
00:22:07.760 can do um uh we can define a call back
00:22:10.440 for that we could be do def. on ticker
00:22:14.559 update eight and then we can do a
00:22:18.520 ticker
00:22:21.200 um and uh you know okay sorry I I'm uh
00:22:25.480 being a little bit messy but I just want
00:22:27.200 to show you guys this EX example so
00:22:29.080 let's assume we're using the exact same
00:22:30.799 example as here okay so let's
00:22:34.760 actually let's make this our
00:22:39.760 example the key the the only goal of
00:22:42.760 this is I do not want you to just
00:22:44.720 blindly place an order with limit price
00:22:47.360 220 I want you guys the limit price to
00:22:49.799 continuously change or do whatever logic
00:22:53.480 we want okay so um let's uh make the the
00:22:58.039 limit be 12
00:23:01.400 24 since 25 since it's after now so I
00:23:05.520 just placed the order and the Order of
00:23:08.120 course is going to be on uh first on
00:23:10.600 pending submit and then presubmit it
00:23:12.200 because we're before the time and look
00:23:15.440 at the limit price of the order if you
00:23:17.720 look at the limit
00:23:19.000 price um you do order. limit price you
00:23:22.640 see it's 1 cent but if we do this call
00:23:26.559 back on ticker update and we do global
00:23:29.840 trade trade. order. liit
00:23:33.480 price equals np. round oh this is why
00:23:36.720 you need NP I noticed that sometimes you
00:23:39.240 do a calculation and and you have a
00:23:41.480 number that's more than two digits it'll
00:23:44.039 be stuck on pending submit forever so
00:23:46.600 that's why you need to have this um uh
00:23:49.640 it's very important to have this um uh
00:23:52.640 NP that round I mean for my experience
00:23:55.520 you could try without it but you might
00:23:57.320 have order stuck on pending submit so
00:23:59.919 now what what it does here is it takes
00:24:01.679 the
00:24:02.440 midpoint um it rounds it to nearest two
00:24:05.880 decimals then it places order let's do
00:24:08.279 midpoint minus uh uh 20
00:24:11.880 cents okay so now you do trade equals
00:24:14.960 ib. place order uh
00:24:18.720 Tesla
00:24:21.480 um um trade.
00:24:23.880 order okay so now let's connect like
00:24:27.320 attach to call back we can do Tesla
00:24:31.080 ticker do um ticker update plus equals
00:24:35.480 on ticker
00:24:37.200 update uh on ticker
00:24:40.039 update oh sorry uh Tesla ticker
00:24:43.559 do uh
00:24:49.440 sorry okay so now we are going to
00:24:54.399 um uh now uh we have uh every time um
00:25:00.399 the Callback automatically changes the
00:25:02.399 limit price so then like order status is
00:25:05.399 pre- submitted because oh it's submitted
00:25:08.039 now because we're after um uh uh
00:25:12.520 12:25 but it's only going to fill when
00:25:15.320 we get to the Limit price so this kind
00:25:17.399 of gives you more control over it when
00:25:19.000 you have a call back and you're
00:25:20.559 calculating here I'm calculating the
00:25:22.080 midpoint of the ticker I want to buy
00:25:24.240 subtracting by
00:25:25.679 02 okay so this is an example
00:25:30.520 so okay so we need to now um um clear uh
00:25:36.760 the um update event uh and we can cancel
00:25:40.399 the open orders um now I'll show you how
00:25:42.880 to combine conditions you can combine
00:25:44.919 multiple conditions so um at first I'm
00:25:47.760 just going to show you how to combine
00:25:49.120 like a um a Time condition plus uh
00:25:52.760 volume condition um so you can have as
00:25:56.520 uh previously we had the um the order
00:26:00.360 and now the conjunction could be an and
00:26:02.880 or an or it would be either a or O So a
00:26:07.360 so what does a mean a is and so both
00:26:10.360 have to be true so let's uh keep the
00:26:13.039 same volume condition we've had
00:26:14.799 previously so um the volume condition is
00:26:18.159 true um and the conjunction here doesn't
00:26:21.440 matter because you only look at the the
00:26:23.799 one before it but I'm appending that so
00:26:26.600 first I append the time condition and
00:26:28.080 the volume condition and this is a a and
00:26:31.440 and since this one is false uh for the
00:26:33.880 next minute um the uh the thing
00:26:37.960 shouldn't Tri um trigger yet so let's
00:26:40.640 try that at first is pending submit and
00:26:43.799 then it's uh pre-submitted
00:26:45.880 54 it it should be pre-submitted until
00:26:48.440 it gets to
00:26:52.399 55 let's wait patiently for this
00:26:56.480 okay um if we were to want to use the or
00:27:00.520 condition we can uh change this to an O
00:27:03.799 but yeah I waited till 55 now it should
00:27:06.200 be filled because that was an and but
00:27:08.399 now it's an or so now just one needs to
00:27:10.960 be true so now let's make it
00:27:12.640 1355 that's way not true but the second
00:27:15.679 one is true uh and this is an or so it
00:27:19.120 should be filled right away PR submitted
00:27:22.279 and
00:27:23.360 then fill great Okay so or fills if just
00:27:29.440 one of the two conditions
00:27:32.240 works you can also combine uh more than
00:27:36.799 uh two conditions so like first I showed
00:27:40.159 you guys um time condition plus volume
00:27:43.640 condition but I can also do time
00:27:45.640 condition plus let's say volume
00:27:48.000 condition one plus volume condition uh
00:27:53.399 two um and then I can do like let's say
00:27:56.120 an or and and then I can do an and or
00:28:00.320 whatever uh just as an example there is
00:28:03.080 this thing like this order of operations
00:28:05.760 thing uh there there's this like rule of
00:28:08.880 what goes first when you do conjunctions
00:28:11.960 um and I I don't think I don't know if
00:28:14.559 there's a way to do parentheses um it's
00:28:16.960 out of the scope of this video I can try
00:28:18.600 to figure it out later but like
00:28:20.640 basically you can have all these like
00:28:22.440 conditions you're going to have like a
00:28:23.760 and b or c and d or e whatever and then
00:28:29.039 there's like an order of operation so
00:28:30.600 apparently from Chad gbt it goes not
00:28:33.440 then and then or so let's see if this
00:28:36.240 actually works so um yeah I do use Chad
00:28:39.480 gbt a lot so let's make a dummy
00:28:41.720 condition where um this thing is false
00:28:46.080 and it's false because it's obviously um
00:28:49.399 uh way before
00:28:51.000 1355 and and uh one of these two is
00:28:54.519 false so the and will be false and let's
00:28:57.120 see if if it if it triggers or not so
00:29:00.720 let's uh let's show this example so
00:29:03.000 let's copy this same thing except let's
00:29:07.519 have uh we'll call it um volume
00:29:10.559 condition
00:29:11.760 one
00:29:14.559 um uh this one is the true one but we'll
00:29:18.039 have the and here and then let's do
00:29:20.000 volume condition two this is the one
00:29:22.720 we're going to make false so let's just
00:29:24.799 make the volume like way way way way
00:29:26.760 bigger
00:29:28.159 so now let's actually see if uh this uh
00:29:32.919 Works um uh what did I get wrong
00:29:37.330 [Music]
00:29:41.600 um maybe maybe uh the uh volume
00:29:45.480 condition is way too big I don't know
00:29:52.919 um is this the condition is this the
00:29:56.320 problem okay so the second one was a
00:29:59.159 problem you know let's just do the same
00:30:01.000 exact one as here but we'll make it like
00:30:03.640 a um is more is false so we want less
00:30:06.840 than volume so obviously you can't have
00:30:08.519 more and less than the same volume so
00:30:10.919 now let's first place the order send
00:30:12.960 pending submit so this is Moment of
00:30:15.279 Truth pres submitted pres submitted so
00:30:18.760 because of the order of operations it I
00:30:21.039 I was doing like the first thing or the
00:30:23.919 second thing and the third thing again
00:30:26.840 the last
00:30:27.760 conjunction doesn't matter um this and
00:30:31.640 happens first so I first do and of these
00:30:33.600 two it becomes something that's not true
00:30:36.360 and then uh the first thing is not true
00:30:38.720 or the second thing is not true it's not
00:30:41.080 true yet so it's a pending submit okay
00:30:44.000 so now um now that we have these
00:30:46.919 conjunctions out of the way let's do um
00:30:50.600 maybe this example will answer um so I
00:30:53.799 hope you guys enjoyed this video please
00:30:55.720 like And subscribe and and send
00:30:57.760 questions thank you
