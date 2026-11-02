
# tactiq.io free youtube transcript

# Trailing Stop Orders with Interactive Brokers API in Python

# https://www.youtube.com/watch/2lboKU1CqOs

00:00:00.880 hey guys welcome to my video in this
00:00:03.280 video I'm going to be talking about how
00:00:04.640 to place trailing stop orders with
00:00:06.960 Interactive Broker API in Python using
00:00:09.679 IB and sync uh it's going to be my first
00:00:12.120 video trying this filter um so let me
00:00:15.200 know how it is with me not having a
00:00:17.439 background um of course like other
00:00:19.840 videos If you enjoyed if it was helpful
00:00:21.840 please like And subscribe it helps a lot
00:00:24.840 um I did want to start by saying like it
00:00:27.000 was really sad news to hear that the
00:00:29.359 author of The IB and sync library AAL
00:00:32.759 dwit unfortunately passed away and his
00:00:35.760 siblings um uh wrote this message it's
00:00:39.239 really sad this guy literally wrote the
00:00:41.559 best library in the world um there are a
00:00:44.440 few people that are going to a lot of
00:00:46.320 people that are going to continue this
00:00:48.160 Library moving forward but it's really
00:00:49.920 sad especially he seemed like a young
00:00:52.320 guy an extremely nice guy uh very sad
00:00:55.120 for all his family and condolences to
00:00:57.160 all his family cuz this library is like
00:00:59.359 the best Li in the world and um and just
00:01:02.559 condolences to his family it was kind of
00:01:04.680 shocking um so yeah um so sad very sad
00:01:09.880 about that um so uh my condolences again
00:01:14.840 okay so uh on that sad note Let's uh
00:01:17.920 maybe get started so we want to talk
00:01:20.439 about how to place trailing stop orders
00:01:23.479 right so um what is a trailing stop
00:01:26.200 order so let's uh give you the case
00:01:29.000 where like you're you you bought the
00:01:31.680 stock you're in the trade and you now
00:01:34.560 want to sell your stock um and uh let's
00:01:38.360 say the stock went in the right
00:01:39.920 direction like the price went up you
00:01:41.600 want to lock in some of those gains so
00:01:43.600 you want the stop loss to follow you so
00:01:46.799 that's what the trailing stop does um so
00:01:49.600 let's say like um assume I I have a
00:01:52.640 trailing stop like I I say like $1 below
00:01:56.600 and I buy Tesla at 180 um uh so and then
00:02:01.200 I submit that uh trailing stop order at
00:02:03.840 180 so um if Tesla goes to 195 my stop
00:02:08.639 now goes down to 194 it always uh
00:02:12.200 follows it up and goes $1 less and you
00:02:15.280 can also specify it as a percent okay so
00:02:18.239 let me show you how to do this with
00:02:19.440 interactive brokers with IB and sync so
00:02:22.200 let's first connect to um
00:02:25.640 IB so let's connect IB um
00:02:31.440 okay so let's define the contract we
00:02:33.560 want to go with um so let's uh like
00:02:36.519 other videos of mine let's define Tesla
00:02:39.200 so we Define it like as stock equals
00:02:41.519 stock symbol exchange currency qualified
00:02:45.080 contracts gives you like additional
00:02:47.159 information like the con ID like the
00:02:48.920 unique stuff but in this case you don't
00:02:50.840 need it I'm just going to request Market
00:02:53.120 data just because it'll help us get
00:02:55.680 intuition of what's going on when we
00:02:58.040 place orders and that sort of thing so
00:02:59.800 so how do we request Market data of
00:03:01.959 course we do this ib. Market data uh we
00:03:05.799 give it a contract generic tickus is
00:03:08.000 what we want to see I just did the
00:03:09.879 default snapshot equals false that means
00:03:12.239 like it'll constantly update regulatory
00:03:14.680 snapshot like you get the national best
00:03:17.319 bid ask uh bid offer thing but we don't
00:03:20.159 need that we don't I mean because it
00:03:21.519 costs money so okay so we Define this
00:03:24.720 ticker to get the market data we also
00:03:27.319 are going to define a um uh a um call
00:03:31.080 back so all this call back is going to
00:03:33.280 do is um I'm going to use it later on
00:03:35.840 but basically it's GNA kind of track the
00:03:38.159 maximum stock price uh so this will kind
00:03:41.280 of help us with the information like so
00:03:43.760 like we when we have a stop uh um sell
00:03:46.720 order um we um track the maximum stock
00:03:50.680 price uh because we know that our uh
00:03:53.560 stop will be like an offset from that
00:03:56.360 maximum so if the maximum gets to like
00:03:58.879 350
00:04:00.439 and our offset is a dollar then um then
00:04:04.200 $3.49 would be the price oh and I did
00:04:07.159 want to make very very clear that I have
00:04:09.959 never used this in real life um and
00:04:12.640 please this is not Financial advice uh
00:04:15.760 please check it a million times I did
00:04:17.798 not use this in real life so please
00:04:20.600 check it a million times before you use
00:04:22.320 it um thank you okay so like what this
00:04:25.759 callback basically will do is and you'll
00:04:28.520 see later on is um I'm going to always
00:04:31.560 Define the max stock price to be zero
00:04:34.000 and a new order whenever there's a new
00:04:35.720 order and all it's going to do is like
00:04:38.160 whenever there's like a ticker that last
00:04:40.840 which is the last trade price whenever
00:04:43.240 it's bigger than the current Max price
00:04:45.199 we set the max price to that price and
00:04:48.039 all that's going to do is just keep
00:04:49.400 track of the max price this is just to
00:04:51.680 help us understand things so let's run
00:04:54.240 this and to chck to call back to the um
00:04:56.440 ticker we do ticker the update event
00:04:58.600 plus equals um on on ticker update and I
00:05:02.560 guess my
00:05:03.880 um okay so just to show you guys like
00:05:06.600 okay so ticker that last for example
00:05:09.280 this is the last uh traded price for
00:05:12.400 Tesla okay so let's now talk about
00:05:15.320 defining a trailing stopper I'm guessing
00:05:18.560 uh um uh that this is usually like in
00:05:22.000 the context of uh a bracket order but
00:05:24.840 we're not going to do the bracket order
00:05:26.479 we're just going to say assume we
00:05:27.960 already made the trade we bought the
00:05:30.039 stock um and now we want to sell the
00:05:32.280 stock uh so we can have the stop order
00:05:35.319 for selling the stock um so first let's
00:05:38.639 go to the documentation uh for uh twws
00:05:41.960 API the IB and sync documentation is
00:05:44.600 very
00:05:45.479 similar I mean it just gives you like
00:05:47.440 the basic things so you see like there's
00:05:49.000 a trailing stop so you should read this
00:05:52.759 to get more
00:05:53.800 information um so you have like action
00:05:56.600 uh order type Trail the key is order
00:06:00.199 type here is Trail uh action is like in
00:06:03.240 all the other actions in my other videos
00:06:05.680 and total quantity is uh quantity uh
00:06:08.960 trailing percent uh is uh the trailing
00:06:12.120 percent and uh trailing stop price is uh
00:06:17.000 uh is okay sorry sorry I lost my tra
00:06:20.120 thought okay so the key thing is the
00:06:22.680 really important thing is you have a
00:06:24.160 trailing either two things you can have
00:06:26.400 either trailing percent or Ox price
00:06:29.720 price um so I wrote it here you can
00:06:32.360 either have a trailing percent or Ox
00:06:34.440 price Ox price is if we um want to do
00:06:38.240 like an actual number so let's say like
00:06:40.840 um you place the or you you want to like
00:06:43.520 the trailing to be like $2 less than the
00:06:46.360 price uh the max the price it goes up to
00:06:49.639 so uh that would be when you'd use Ox
00:06:52.440 price you'd use trailing percent if you
00:06:54.639 say like okay um um as long as it goes
00:06:57.919 up I move my stop to like a certain
00:07:01.160 percent below the the price it got to so
00:07:04.120 that would be uh the trailing percent so
00:07:06.160 use either one of these to the other
00:07:09.440 small thing I wanted to say is
00:07:10.759 regardless of anything there's a thing
00:07:12.160 called Trail stop price this would be
00:07:14.080 like an absolute price to use um and
00:07:17.000 I'll show you guys in an example later
00:07:19.039 so actually maybe I'll just um show you
00:07:22.720 guys right now an example so what is
00:07:25.440 Tesla right now Tesla's at um
00:07:28.520 171.5 9 right so if I were to um do uh
00:07:33.879 this order I would do order equals order
00:07:36.599 order type equals Trail action sell it's
00:07:39.680 going to be a sell stop Ox price equals
00:07:42.039 let's just do 5.5 so this is like far
00:07:45.680 away but I'll put a trail stop price at
00:07:49.960 um let's just put it at like 70
00:07:54.080 171.5 just to show you guys because this
00:07:56.319 is like the the regular stop as if like
00:07:59.720 you forget the trailing stop this acts
00:08:01.759 like a regular stop I'll put it 17 1.55
00:08:04.840 so then I place this order and then I do
00:08:07.680 trade. order status I look at the order
00:08:11.199 status it's pre-submitted it's still
00:08:13.800 pre-submitted because it it's above
00:08:16.280 171.5 five and once it falls to
00:08:20.319 17155 you'll see that it's
00:08:23.520 um that it'll be filled because this is
00:08:26.159 like this is like the stop price
00:08:28.039 regardless and this is for sell
00:08:30.240 uh for buy it'll be the opposite
00:08:31.879 direction it's like when the price goes
00:08:33.479 High you buy uh okay so um oh so you
00:08:38.519 know what forget this let's cancel
00:08:40.279 orders for o o n IB do open
00:08:45.480 orders uh let's do uh ib.
00:08:51.880 cancel order
00:08:54.480 O Okay so I cancel this order so let's
00:08:58.320 do again uh let's do one that'll
00:09:00.160 actually hit let's do
00:09:02.800 171.5 okay so now the order status is
00:09:05.279 presubmit presubmit and if it goes below
00:09:09.000 oh now it should be filled because it
00:09:10.240 went below 171.5 see filled okay so
00:09:13.760 that's just saying that this is the
00:09:15.040 regular stop so now let's actually go to
00:09:17.519 the actual trailing stop okay so let's
00:09:20.839 actually Define a callback to help us
00:09:23.040 understand what's going on so uh we can
00:09:25.440 define a callback uh uh I'll call it on
00:09:28.480 fill event
00:09:30.200 um so like what what's going to happen
00:09:33.279 is I'm going to attach this call back to
00:09:35.240 the uh trade the order I I I've just
00:09:38.320 placed and uh when it gets filled it's
00:09:41.200 going to print the um execution price uh
00:09:44.880 which is like the price where um this
00:09:47.160 got filled the max stock price um and
00:09:50.839 the initial stock price just to give us
00:09:52.760 an intuition so uh we're going to then
00:09:55.880 create this function to create a trade
00:09:58.760 um so look at this function here it's
00:10:00.200 going to just oh oops sorry this
00:10:02.720 function is going to just be um the
00:10:05.480 regular ib. place order except um uh I'm
00:10:10.360 uh now uh having uh a
00:10:15.600 uh I'm adding the call back I'm
00:10:18.000 attaching the call back right away soill
00:10:20.440 event plus equals unfilled event and I
00:10:23.440 have another video about this stuff I
00:10:25.920 guess I should refer you guys to like uh
00:10:27.959 my IB in sync uh playlist has a lot of
00:10:30.839 these videos but okay so so now let's
00:10:33.959 Show an example on how this is used so
00:10:36.360 like let's say we have the order and
00:10:38.720 let's say we we our trailing stop will
00:10:40.839 be 02 uh uh like 0 2 so like we can
00:10:45.000 place the order we can do like order uh
00:10:48.279 order type Trail uh action sell total
00:10:51.440 quantity is 100 Ox price equal 02 so
00:10:54.320 this will be Trail uh and 02 below like
00:10:57.320 the max price it got to and uh if you
00:11:00.000 don't specify this uh Trail stop price
00:11:03.519 then um then like it you just don't have
00:11:07.000 it so this is just just a trailing uh
00:11:09.480 stop price okay so uh now I'm going to
00:11:12.519 do this place order with callback and
00:11:14.839 then I'm going to set this uh New Order
00:11:16.800 flag to true and the initial stock price
00:11:20.360 to
00:11:21.440 um I mean you don't really need this the
00:11:23.639 New Order flag just helps me with the
00:11:26.079 first call back to keep track of the
00:11:27.839 maximum price just kind of to help us
00:11:30.000 out so like okay so um here what
00:11:33.279 happened is I placed the order uh my my
00:11:36.279 trailing stop is point2 wow Tesla just
00:11:39.160 jumped uh so um
00:11:42.839 so and when it gets filled it's going to
00:11:45.440 print the maximum stock price and the
00:11:48.560 execution price so we should expect the
00:11:50.920 execution price to be roughly uh 02 less
00:11:54.680 than the maximum stock price because we
00:11:56.800 trailed it up to 02 below so so this is
00:11:59.639 like uh let me maybe I'll say this like
00:12:02.399 a um uh
00:12:05.040 absolute
00:12:07.519 trailing stop
00:12:10.399 amount um and one second this uh what do
00:12:14.120 they call it specifically they call it
00:12:15.560 like um oh Trail amount or Trail
00:12:18.920 percentage okay so I guess Tesla
00:12:21.160 actually went up uh oh so it should okay
00:12:25.120 great uh well I made I made so I I I
00:12:28.160 made a typo but this is what I wanted to
00:12:30.160 say is like um it got the price got up
00:12:33.199 to
00:12:42.360 172.72cm Market order that by the way
00:12:46.079 the reason this is uh uh a difference of
00:12:49.320 25 here is because of course um stop
00:12:52.920 orders are Market orders there's also by
00:12:55.120 the way a stop a trailing stop limit
00:12:57.680 where if you if you want like a limit
00:13:00.079 also like um because if the stock were
00:13:03.279 to jump uh like um dropped like $20 it
00:13:07.720 right away will execute because a stop
00:13:10.079 order is actually a market order once
00:13:11.800 the price gets filled so uh I guess I
00:13:14.480 made a typo initial stock
00:13:19.920 price uh okay so uh anyways uh forget
00:13:24.560 this typo for a second okay so this is
00:13:26.880 the example with an absolute amount um
00:13:29.680 if you want to example with a percent
00:13:33.320 amount
00:13:41.000 uh okay so let's just uh see for a
00:13:43.519 second what's the price it's about 172.2
00:13:46.600 so let's do a percent amount to like uh
00:13:49.399 let's do 0.1% okay so now it's similar
00:13:52.800 to here except the order will now
00:13:54.720 instead of do using Ox price we're going
00:13:57.040 to use uh uh Trail
00:13:59.759 link percent and let's do uh um Point uh
00:14:04.759 you know what let let me just uh make
00:14:06.240 sure for a second that sometimes these
00:14:08.639 things are a little bit tricky like with
00:14:10.680 absolute numbers I think this would be a
00:14:13.800 a
00:14:14.800 um a a0 1% change but let me double
00:14:20.279 check because if it's uh Point sorry
00:14:23.720 this would be a 0.01% change but let me
00:14:26.800 double check cuz if it's not a 01 %
00:14:29.519 change it'll be a 1% change so like if
00:14:32.360 it's a 0.01% change it'll fill right
00:14:34.600 away if it's a 1% change it'll take some
00:14:37.680 time so let's just see if that worked um
00:14:40.440 so uh let's just make
00:14:43.839 sure uh uh so I I do like
00:14:49.480 this so uh let's see if this would be a
00:14:53.160 .01% or a
00:14:55.519 1%
00:14:57.240 um so last is uh this so I think this is
00:15:02.600 a .01% change so yeah exactly what I
00:15:06.399 thought um so um yeah so this is a 0.01%
00:15:11.160 change so when we want like a 0.1%
00:15:13.680 change it'll go like we do this
00:15:15.839 thing
00:15:17.480 um so oh I spelled initial wrong that's
00:15:21.240 why okay um so now this is a 0.1% change
00:15:26.600 so so let me write in this example like
00:15:28.639 a
00:15:32.160 um a .1%
00:15:36.880 change not a 0.01
00:15:41.680 change and here I'll I'll write a um
00:15:45.319 amount of uh 20 cents okay so this is
00:15:49.000 like a 0.1% change so let's say like
00:15:52.639 Tesla is like here
00:15:57.920 171.8cm way 171 97 is the current market
00:16:02.680 price uh but it's
00:16:04.800 .1% so um so 1% is about $1.70 so 0.1%
00:16:10.800 is about
00:16:12.360 17 uh
00:16:22.920 cents okay so uh it's about 17 cents so
00:16:27.040 this is the actual percent again um
00:16:30.240 again I I have never used this in uh in
00:16:32.639 my real trading so um uh please uh
00:16:38.000 double check and do not use it right
00:16:39.959 away okay so that so we have that okay
00:16:43.639 so now uh I wanted to say one thing so
00:16:45.920 now that we've talked about trailing
00:16:47.199 stops let's talk about um so like you
00:16:50.800 probably would want it as part of a
00:16:52.160 bracket order meaning let's say you buy
00:16:54.279 the stock and then you have a limit
00:16:55.800 which is your take profit and then you
00:16:57.600 have your stop loss which is you're like
00:16:59.639 uh instead of a stop loss you'll have a
00:17:01.639 stop limit or I sorry you'll have a
00:17:03.680 trailing stop so like it could be so I
00:17:06.480 just wanted to say is like what I
00:17:08.400 recommend is like once if you use like a
00:17:11.199 ID like py charm you can uh do from IB
00:17:15.079 sync import Star IB equals IB and then
00:17:18.520 you can look there's a function called
00:17:20.000 ib. bracket order do jump to declaration
00:17:23.119 control B in in py charm and you see its
00:17:25.679 function it gives you like a parent a
00:17:28.119 takeprofit and the stop loss so this is
00:17:30.679 the bracket order and then you actually
00:17:33.320 Loop through this order one by one and
00:17:35.760 you like submit the parent the take
00:17:37.760 profit and the stop loss so um just to
00:17:40.400 show you guys like uh for a second so um
00:17:44.000 I uh have
00:17:46.200 um okay let me just write this so um
00:17:50.559 oops where would we go okay so like
00:17:56.720 um so like okay so you you can Define
00:17:59.720 like a a custom Brack order bracket
00:18:01.960 order to fit your needs um I am not
00:18:05.039 going to do this in this video uh but we
00:18:07.559 can do it eventually um I have an a
00:18:10.280 video here about this bracket order so
00:18:12.559 if I do like control this I can get to
00:18:15.280 it um I have a thing I don't get why uh
00:18:18.880 I have commercials they don't uh they
00:18:21.120 don't monetize me um yeah so it's like a
00:18:24.159 double whammy anyways um so uh so yeah
00:18:28.039 this is like talk about bracket orders
00:18:29.760 and parent orders and that sort of thing
00:18:31.799 but I think uh I I don't want to get
00:18:33.720 into details because I just don't have
00:18:35.320 time but like the the the the more of
00:18:37.039 the story is like you have a parent
00:18:39.200 order let's say you're buying the stock
00:18:41.360 and then you have and then that has two
00:18:43.320 CH child orders the take profit and the
00:18:45.280 stop loss but here we would want to
00:18:47.640 change the take Prof the stop loss with
00:18:49.679 the uh trailing stop loss right um so
00:18:53.799 we'd have to change this with a trailing
00:18:55.480 stop loss and then once we have this
00:18:57.400 bracket order we would lose over like
00:18:59.559 the elements in the bracket order so um
00:19:03.799 so uh and and we would place the order
00:19:06.240 individually see please see this video
00:19:08.320 for more details um but like I yeah I
00:19:11.240 don't want to get to Too Much details
00:19:12.520 just to remind you guys like uh the
00:19:14.840 parent order uh um has a transmit equals
00:19:18.600 false the first uh child order um points
00:19:22.799 to the parent order it says parent ID
00:19:24.520 equals parent. order ID as you see and
00:19:28.000 the second child order has parent. order
00:19:30.400 ID but note that the F the parent order
00:19:33.440 and the first child order have transmit
00:19:35.720 equals false and then only the second
00:19:38.440 the last child order has transmitt
00:19:39.919 equals true what this does is it
00:19:41.799 basically kind of says like okay let's
00:19:43.840 wait until uh we we we got all the
00:19:46.960 instructions before we transmit it's
00:19:49.200 it's saying don't just like transmit
00:19:50.880 these before you you get this
00:19:53.280 information so more info is in this
00:19:56.000 video hope you enjoyed this video uh
00:19:58.720 please like And subscribe my condolences
00:20:01.440 to um AAL dewitz family uh really sad um
00:20:06.080 he made the best Library um all the best
00:20:08.960 see you guys in the next video um maybe
00:20:11.240 just one one more small thing is I was
00:20:14.000 able to um make a playlist of i'b and
00:20:18.400 sync things it's not organized uh I
00:20:22.000 probably should just um maybe I should
00:20:25.080 like delete everything and and start
00:20:27.159 from scratch uh making like nice things
00:20:30.320 but I have this like IB and sync
00:20:32.000 playlist um um and uh if you guys want
00:20:35.440 to learn about IB and sync you can try
00:20:37.360 that um hope this was helpful thank you
00:20:40.000 so much have a great
00:20:46.159 day
