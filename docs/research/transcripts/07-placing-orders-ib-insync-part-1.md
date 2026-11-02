
# tactiq.io free youtube transcript

# Placing Orders on Interactive Brokers API Using IB Insync (Part 1)

# https://www.youtube.com/watch/uS4guClUUgE

00:00:01.590 [Music]
00:00:06.480 all right so I'm going to be talking
00:00:07.720 about how to submit an order through IB
00:00:11.920 in sync for interactive brokers so IB in
00:00:15.839 sync is a wrapper for their API uh
00:00:19.279 really bunch of fancy jargon which means
00:00:21.680 that we're able to uh computer code to
00:00:27.359 place orders on interactive brokers
00:00:31.199 couple things you're going to need first
00:00:32.598 you're going to need to download python
00:00:35.120 you're going to also need to download IB
00:00:36.840 and sync and you can find it by Googling
00:00:40.800 IB and sync like like that and then we
00:00:43.079 got GitHub over here this is the
00:00:48.920 project come down and install it on your
00:00:51.680 computer through that right
00:00:53.879 there second thing we're going to need
00:00:56.440 is an Interactive Broker account and
00:00:59.239 then we're also going to have to
00:01:00.399 subscribe to data subscriptions and so
00:01:03.559 uh my ones I'm subscribed to and
00:01:05.720 recommend are these right here in order
00:01:09.000 to do this you have to fund the account
00:01:11.000 and it I believe it has to be at least
00:01:14.680 $2,000 so um that's something that has
00:01:17.720 to be done and then you'll subscribe to
00:01:20.520 these I've got us security snapshot
00:01:23.439 future values bundle then I've got the
00:01:25.759 US equity and options add-on streaming
00:01:28.200 bundle
00:01:30.159 and a CBO E1 add-on bundle these are the
00:01:32.720 ones I have I recommend you may be able
00:01:35.159 to do it with something different but
00:01:37.439 these are ones I have and
00:01:40.399 recommend all right so I'm over here in
00:01:43.320 Visual Studio code let's go ahead and
00:01:45.079 get started so the first thing I'm going
00:01:47.040 to do is I'm going to import IB and
00:01:53.840 sync I'm going say from IB insync import
00:01:57.640 Star I'm also going to import random
00:02:00.200 we'll see what we're going to do with
00:02:01.640 that in a
00:02:03.280 minute that comes with python and so the
00:02:07.000 first thing we have to do is connect to
00:02:08.239 interactive brokers so I'm going to copy
00:02:10.520 over some code here you can see here
00:02:14.000 I've got this random right down here you
00:02:16.519 could put one right here it'll be fine
00:02:19.840 um I've been experimenting with this to
00:02:22.560 see if it speeds up uh any any speed
00:02:26.239 performance uh it doesn't look like it
00:02:28.360 does but I keep it there
00:02:30.560 anyway so the first thing we're going to
00:02:32.519 do IB equals IB and then ib. connect the
00:02:37.000 important thing on this line is this
00:02:38.720 second number right here is 7496 because
00:02:42.560 sometimes this will be
00:02:44.080 7497 um and it won't work and so this
00:02:47.360 number right here has to match our
00:02:49.120 socket port in the trader workstation so
00:02:52.599 if we come over here to the trader
00:02:55.440 workstation and I may not have mentioned
00:02:57.959 another requirement is that we also have
00:03:00.360 Trader workstation up and running when
00:03:02.640 we're running this code it has to be
00:03:04.640 running in the background and so I've
00:03:06.519 got that up here and you can see here
00:03:09.840 under what did we do file Global
00:03:13.799 configurations API settings the socket
00:03:17.840 Port right here is set to 7496 and so
00:03:20.480 those match if those don't match though
00:03:22.799 the code won't work so you got to make
00:03:24.200 sure that those
00:03:26.239 match apply okay then we can minimize it
00:03:30.640 to the background
00:03:32.439 again so once those match we can begin
00:03:35.680 by coding it up what I'm going to show
00:03:37.920 first is just a real basic way that you
00:03:40.360 could do it if you were during the
00:03:43.040 regular trading hours now this won't
00:03:45.000 work in the pre-market or the after
00:03:47.879 hours but this will work during the
00:03:49.920 regular trading hours so first thing we
00:03:52.400 would say is
00:03:53.760 stock and now we can't in this we can't
00:03:57.480 just say the ticker name we can't say
00:03:59.159 hey this is Tesla it's not going to
00:04:01.439 understand what you're saying we have to
00:04:02.560 format it in a certain way and so this
00:04:04.680 is how you format it we're going to do
00:04:11.680 stock first parameter
00:04:14.360 symbol we're going to say
00:04:17.478 Tesla our
00:04:19.478 exchange it's going to be smart
00:04:22.479 slmx now you'll see online some people
00:04:25.160 would do SM just smart and even IB says
00:04:29.120 to use just smart uh I've tested this
00:04:32.120 for a while and when you use just smart
00:04:35.120 sometimes the tickers won't work so the
00:04:37.520 one that I found works for the most
00:04:40.199 amount of tickers is smart
00:04:42.479 slmx and so after that we're going to do
00:04:47.520 currency go US Dollars okay so now
00:04:50.120 that's formatted correctly second part
00:04:52.840 is we have to tell it what we want it to
00:04:54.520 do so we want it
00:04:58.039 to action is going to be uh to submit a
00:05:01.840 market
00:05:05.960 order our action is going to be to
00:05:10.759 buy the quantity is going to be one
00:05:13.720 share and then Tif stands for time and
00:05:16.919 force what this will do is it defaults
00:05:20.280 to where it'll cancel the order at the
00:05:22.560 end of the day if it hasn't filled um so
00:05:25.280 I'm specifying GTC which stands for good
00:05:27.759 to close which means that that it'll
00:05:30.680 stay open perpetually until it gets
00:05:33.919 filled and then to place the order we'll
00:05:36.240 come down here and say order equals ib.
00:05:40.000 place
00:05:41.000 order tell it the stock tell it the
00:05:45.120 action and then we should be good to go
00:05:47.479 so uh when you run this during the
00:05:50.639 regular trading hours um this uh should
00:05:54.759 place the order we can go ahead and run
00:05:56.160 it now it'll it'll send the order to
00:06:00.479 uh Trader
00:06:01.600 workstation but let
00:06:06.919 see all right case sensitive here got to
00:06:09.520 make sure that it's a lowercase
00:06:13.120 p uh so it's going to be a lowercase
00:06:15.919 place and then a capital o on the order
00:06:19.800 go ahead and run
00:06:22.800 this so if I come here I should
00:06:27.000 see that it submitted that Tesla
00:06:30.199 but it's
00:06:33.199 currently being held in monitor that
00:06:35.599 means it's not active and so if you come
00:06:38.039 over here what you'll find is uh
00:06:41.639 currently it's 5:00 a.m. right now so
00:06:43.520 we're in the
00:06:44.639 pre-market if you come here and try to
00:06:47.039 submit a market order and you come here
00:06:49.680 to where it says day probably say day on
00:06:52.720 yours you'll see this fill outside rth
00:06:55.840 and it be gray out you won't be able to
00:06:57.720 click it okay so this is the reason why
00:07:00.639 this doesn't work during the pre-market
00:07:02.120 or the after hours because it does not
00:07:04.160 allow you to submit Market orders during
00:07:06.759 those times if I had to guess why I
00:07:09.720 would say that because the spread gets
00:07:12.280 very wide during the pre-market and the
00:07:14.879 after hours there's not as much
00:07:17.199 liquidity as there is in the regular
00:07:19.840 hours and so they don't want people to
00:07:22.919 submit Market orders and end up losing
00:07:25.639 money um they want you to make sure that
00:07:28.080 you know exactly what you want to buy it
00:07:30.039 or sell it for if I had to guess but
00:07:33.080 they don't allow you to do that so we
00:07:34.560 can only use a limit order you can come
00:07:36.759 here and then you'll choose you can
00:07:38.800 check that box down there so I would
00:07:41.000 check GTC and fill outside
00:07:45.960 rth so to do this in IB and sync we're
00:07:48.840 going to have to change around this
00:07:49.960 action here and so we're going to erase
00:07:52.240 the market order and we're going to call
00:07:54.400 just
00:07:55.280 order and our first parameter is going
00:07:57.599 to be action
00:07:59.879 equals we're going to buy the
00:08:03.440 stock total quantity is going to equal
00:08:07.000 one our order type this is where we
00:08:09.680 specify that we want a limit order
00:08:13.440 LMT so now that we've specified a limit
00:08:16.199 order it wants us to tell it what price
00:08:20.520 do we want it to fill at so I'm going to
00:08:22.720 put a placeholder here for the time
00:08:27.000 being Tif
00:08:29.680 time en Force equals good to
00:08:32.440 close and then lastly we're going to say
00:08:35.039 outside rth stands for regular trading
00:08:38.200 hours we're going to say
00:08:43.000 true so now I have to update that limit
00:08:45.480 order and if I want it to fill right
00:08:46.920 away I'm going to have to do something
00:08:49.360 below the bid so the bid right here
00:08:52.640 209.50 so let's come back in here and
00:08:54.959 we'll change this
00:08:57.839 209 85
00:09:00.440 we'll run
00:09:06.320 this okay I put it should be LMT price
00:09:09.720 right there run that one more
00:09:16.480 time all right so this has to be
00:09:19.440 lowercase th so you can see how
00:09:22.480 sensitive the case is here have to be
00:09:24.920 careful make sure that uh we're
00:09:27.399 following the documentation and so you
00:09:29.920 can find the
00:09:31.040 documentation by Googling IB and
00:09:36.440 sync I'm trying to do this quick and so
00:09:39.000 I'm making syntax errors but um this is
00:09:41.680 where you go to find the documentation
00:09:43.839 and you can figure out exactly what
00:09:45.240 syntax they
00:09:46.480 want all right so now that we've got
00:09:48.399 that we can go ahead and submit
00:09:51.680 it all right so we I don't know if you
00:09:54.200 just heard that but it just went ahead
00:09:55.399 and filled it
00:09:57.959 for come over
00:10:03.360 here there we go so we just got a fill
00:10:06.200 there uh and so we now have one position
00:10:09.640 of
00:10:12.519 Tesla so now what we want to do is we
00:10:14.760 want to sell that share and so we can do
00:10:17.240 that by changing this to sell and then
00:10:19.519 updating this price and I'm going to put
00:10:22.040 a price that's just
00:10:23.680 above the ask and if we run this it
00:10:28.079 should sell it
00:10:32.519 come back over here and again it's not
00:10:34.519 always immediate sometimes it is
00:10:36.079 immediate other times it takes it a
00:10:38.200 while we can see it submitted it and
00:10:40.600 it's currently active and waiting to be
00:10:44.480 filled so that'll fill sometime soon see
00:10:47.880 what
00:10:49.920 the
00:10:57.360 20990 okay it's not filling cuz I put a
00:10:59.760 price that's higher so let's do the bid
00:11:01.480 there update that that should
00:11:07.720 F and so that sort of highlights the big
00:11:10.279 issue here is that we don't want to keep
00:11:12.279 having to enter in our limit prices
00:11:14.800 every single time and so what we can do
00:11:17.240 is we can edit this round to where it'll
00:11:19.959 automatically submit an order uh that is
00:11:24.200 equal to the bid price and then sell it
00:11:26.560 that's equal to the ask and so this is
00:11:30.000 the same thing as a market order where
00:11:32.480 we're losing the amount of the spread uh
00:11:35.480 but it's going to make it to where we
00:11:36.760 don't have to enter a
00:11:41.079 number another thing we want to do is
00:11:43.639 we're going to put this uh into a
00:11:46.200 variable and we want two variables here
00:11:48.959 buy stock and sell stock uh so that we
00:11:51.760 can call these uh I don't know what you
00:11:55.480 call them like functions uh to to get
00:11:58.440 them to buy the stock and then sell the
00:12:00.519 stock when we want and so to do that
00:12:02.480 we're going to come here up here to the
00:12:04.120 top right below connecting interactive
00:12:05.839 brokers and we're going to say Define
00:12:08.959 we're going to call
00:12:10.920 this by
00:12:15.959 stock and we're going to place this
00:12:19.920 action inside of it so what this does is
00:12:22.760 this is like
00:12:26.560 um you can think of this as like storage
00:12:30.480 so we're saying whenever we type in byy
00:12:33.959 stock with those two parentheses we want
00:12:37.720 it to run this code that's
00:12:40.760 indentured uh to the right underneath
00:12:44.120 this byy stock and so we're going to say
00:12:45.720 the action is going to be order
00:12:47.680 here and then we're going to want it to
00:12:50.240 place that order as
00:12:57.240 well and then on the reverse first we're
00:12:59.639 going to copy this contrl C to copy come
00:13:02.160 down here paste this in we want it to
00:13:05.120 sell stock and then all we have to do is
00:13:07.959 just change this little action right
00:13:09.279 here and so up here I got to change this
00:13:11.000 to
00:13:12.839 buy and so now when we go down here and
00:13:16.079 type in buy
00:13:18.399 stock or sell
00:13:20.760 stock it'll run this code without us
00:13:23.320 having to retype all of
00:13:28.120 this all right so now that we've gotten
00:13:30.120 that in there I'm going to erase the
00:13:31.639 action I'll also erase place order we'll
00:13:35.079 leave the stock outside of
00:13:38.040 it and what we'll do to access the bid
00:13:41.600 and the ask we'll come down here and
00:13:44.240 go data equals ib.
00:13:48.639 req capital M
00:13:51.279 KD capital D
00:13:54.199 ATA Quest Market data this is going to
00:13:57.560 have four parameters
00:14:00.079 contract is going to equal our
00:14:05.440 stock generic tick list we're going to
00:14:08.240 leave this blank we're going to put
00:14:10.720 two apostrophes there comma this next
00:14:14.959 one right here is called snapshot and
00:14:16.880 what this does is um my understanding of
00:14:21.000 what this is is it just Returns the data
00:14:24.040 once and if this were true then you're
00:14:26.600 only going to be able to return it once
00:14:28.920 um if you want to have a Perpetual flow
00:14:33.000 of Market data you would want this to be
00:14:35.279 false and then we would set up the code
00:14:37.440 a little differently what we're doing is
00:14:39.720 we're only going to request it once so
00:14:41.480 we could have this true uh but just for
00:14:45.120 E's I'm going to say snapshot equals
00:14:47.279 false it'll still will still run the
00:14:49.560 code and have the same effect as if it
00:14:52.120 were true um but this is uh avoiding
00:14:56.240 issues when you do want a perpetual flow
00:14:59.320 of data and then regulatory snapshot
00:15:01.759 down here and we want this to be false
00:15:03.880 because uh if you do this snapshot they
00:15:07.040 charge you uh money and so we wanted
00:15:09.800 that to be
00:15:11.720 false after that we want it to it has to
00:15:14.600 have to wait a second if you come in
00:15:17.000 here to the
00:15:18.160 documentation to request Market data
00:15:20.839 you'll read wherever it's
00:15:24.720 at let's see if I find it here there we
00:15:28.319 go get tick of the given
00:15:31.279 contract it must have been requested
00:15:33.480 okay the ticker may not be ready yet if
00:15:35.759 called directly after okay so we have to
00:15:39.360 wait amount of time in order for this to
00:15:42.120 work so we're going to say ib.
00:15:44.480 sleep we're going to give it one
00:15:50.360 second and then what we'll want it to do
00:15:53.360 after we've gotten that data is we want
00:15:55.120 it to buy the
00:15:56.440 stock so
00:15:59.639 and so let's wait on that so let's ahead
00:16:01.560 and run this and what we'll
00:16:04.639 see if we run this we can look down
00:16:07.079 below here in the terminal what we
00:16:09.319 should see
00:16:11.399 is oh sorry I didn't print then we have
00:16:14.720 to print the
00:16:16.680 data let's go Ahad and run
00:16:21.040 that all right so right down here is the
00:16:23.600 information that is returned and we can
00:16:26.600 see in this thing that we have the bid
00:16:29.360 right here of 210 and the ask of
00:16:33.800 210.8 so what we want to do is when we
00:16:36.639 run this we want it to take this bid
00:16:39.639 take this ask and put that number into
00:16:43.120 our action up here at the top and so to
00:16:47.120 do that we'll say on these numbers for
00:16:51.399 the buy we want it to want it to buy it
00:16:53.759 at the
00:16:55.079 cheapest
00:16:56.600 uh or the most expensive one possible so
00:17:00.120 that's going to be data. ask and then
00:17:03.000 we're going to sell it at the cheapest
00:17:05.880 one possible and this the same thing as
00:17:07.880 a market order where we just want it to
00:17:10.679 get filled immediately we don't care
00:17:12.400 about uh the best price that's going to
00:17:15.799 be data.
00:17:20.599 bid I'll get rid of this
00:17:23.000 print and what we'll do now is we'll buy
00:17:27.000 stock requesting that buy the stock
00:17:30.600 we'll have it
00:17:33.160 wait 15
00:17:35.280 seconds and then we'll have it sell the
00:17:45.840 stock all right so let's go ahead and
00:17:47.720 give this a
00:17:54.440 run all right so if we come over here
00:17:59.679 you can see that submitted it and it
00:18:01.120 just filled right there and so it bought
00:18:03.799 it and now we're waiting on it to sell
00:18:07.919 it there we go it just sold it at
00:18:11.440 20999 we can come in here and see these
00:18:15.200 things right here so we had
00:18:18.720 our it bought it 21.9 and sold at
00:18:23.760 20999 so we lost that spread but again
00:18:26.840 you can see we got it filled and we sold
00:18:29.400 it in a relatively short
00:18:32.880 order and so from here this gives you a
00:18:35.320 good base to where you can start trying
00:18:37.840 to program it to do strategies so we can
00:18:40.960 we have it right here where we're
00:18:41.960 waiting 15 seconds but uh really the sky
00:18:45.000 the limit as far as what strategies you
00:18:47.799 want to program to when this thing buys
00:18:50.039 the stock and when it sells the stock
