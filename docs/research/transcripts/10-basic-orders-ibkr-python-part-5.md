
# tactiq.io free youtube transcript

# Effortlessly Place Basic Orders with Interactive Brokers Python API-Part 5

# https://www.youtube.com/watch/1t_YtxlXuQs

00:00:01.560 hi everyone so today we will be
00:00:03.840 discussing about how we can place
00:00:05.580 different types of order on IBK so
00:00:08.760 before showing you how to do via API
00:00:11.400 first let me show you how we can do
00:00:12.840 manually so right now the Indian market
00:00:14.880 is active so let me place an order on
00:00:17.760 Indian market let's say we want to trade
00:00:20.420 TCS okay now when I click on TCS on the
00:00:24.060 left side you can see this order window
00:00:25.560 bar so here first I have to specify the
00:00:28.260 quantity let's say I want to trade One
00:00:30.180 stock I want to buy the stock now I have
00:00:33.120 to specify is it a market price or at a
00:00:35.399 limit price so let's say I want to place
00:00:36.899 an order at a market price
00:00:38.940 then I just have to click on submit now
00:00:41.879 the moment I click on submit there will
00:00:43.620 be an active order once the order is
00:00:46.379 filled that order will be converted to a
00:00:48.840 trade okay so right now I have three
00:00:51.059 trades now let me just click on the
00:00:53.100 button and show you over canceled so
00:00:55.379 your order is not accepted
00:00:59.579 okay
00:01:02.640 I think I have placed on a different
00:01:05.040 stock this is not an NSE stock so I have
00:01:07.920 to search for TCS NSE
00:01:11.340 or let's say I will trade on sdfc okay
00:01:14.340 instead of NSE let's do it on HDFC click
00:01:16.920 on Buy I'll have one
00:01:20.520 and let's do a market order and I'll
00:01:23.100 click on submit
00:01:25.020 you see the order was placed and you can
00:01:27.360 see it is showing order filled also
00:01:29.820 so what happens whenever you place an
00:01:32.400 order first it comes in the order window
00:01:34.500 once it is filled it will go to the
00:01:36.900 trade window
00:01:38.040 okay and if it is properly filled you
00:01:40.860 should be able to see the same stock in
00:01:42.900 your portfolio also right now you can
00:01:44.520 see in my portfolio I have HDFC
00:01:47.939 okay so this is how you can place a
00:01:49.979 trade manually now I'll show you how do
00:01:52.560 you place a similar type of trade by
00:01:54.899 using python
00:01:56.820 so let's make a new file first so I'll
00:01:59.220 make
00:02:00.720 orders.py
00:02:03.479 so let me just copy the code that we
00:02:05.460 have written in our last session I'll
00:02:07.320 copy this
00:02:09.419 I'll just paste it here
00:02:11.640 I'll just remove this code and we don't
00:02:14.580 want any Forex talk let's go for a
00:02:17.700 normal stock so I'll write stock
00:02:19.739 and now to specify the name of the stock
00:02:21.620 now I let's take TCS okay now one more
00:02:26.580 thing I have not told you in the
00:02:28.140 contract uh lecture that is it is fine
00:02:31.560 even if you specify only the name of the
00:02:33.599 stock okay here I have specified TCS so
00:02:36.480 it will directly make a contract for TCS
00:02:38.400 I don't have to specify the exchange and
00:02:40.560 the currency you can specify it but it's
00:02:42.360 not mandatory so I'll just show you I'll
00:02:45.420 write contract is equal to IB dot
00:02:48.480 qualify contract
00:02:50.099 we will sign the same contract in this
00:02:52.319 square bracket 0 because it's a list and
00:02:55.319 the next line I'll just print the
00:02:56.819 contract so if I run the code I should
00:02:58.920 get the TCS contract
00:03:01.620 okay it is saying list index out of
00:03:03.599 range so there are multiple TCS okay
00:03:05.640 that's why it is not working let's go
00:03:07.260 for HDFC so see the problem with this
00:03:10.860 type of syntax that is if you only
00:03:12.840 specify the name of the stock so if that
00:03:15.780 stock is trading in multiple exchange
00:03:18.060 then it will throw an error not an error
00:03:20.519 like it will give you all the contract
00:03:22.620 but if it trades only in single market
00:03:24.840 then it is not going to uh you know
00:03:27.180 cause any problem so let me show you
00:03:28.920 another example let's take example of
00:03:30.720 reliance
00:03:33.720 now if I run the code now this stock is
00:03:35.700 only trading in the Indian market so you
00:03:37.560 can see I've got the only single
00:03:39.780 or a single contract okay now let's take
00:03:42.480 some other stock like sdfc
00:03:45.599 now if HDFC is traded only in Indian
00:03:47.519 stock it will give me a single contract
00:03:49.500 yeah so you can see it is giving me a
00:03:51.000 single contract so I was successful in
00:03:53.280 making the contract now after making the
00:03:55.440 contract I have to make a order class
00:03:57.480 now when it comes to order class
00:03:59.940 you have to understand
00:04:02.280 that there are two types of uh classes
00:04:05.159 that are available for us okay one is
00:04:07.319 for a few classes that are provided by
00:04:09.599 IBN sync and that is one
00:04:12.120 class which is provided by the IB
00:04:14.400 official documentation so this order
00:04:16.079 class is provided by official
00:04:17.760 documentation and this Market order in
00:04:20.040 limit order class are provided by IBN
00:04:22.380 sync so I'll show you all three of them
00:04:24.300 so first let me use this Market order
00:04:27.419 so what I'll do I'll simply write Ord
00:04:32.460 is equal to Market order
00:04:35.520 in Market order I have to specify two
00:04:37.259 things one is the action and one is the
00:04:38.880 quantity action means do I want to buy
00:04:40.620 or sell let's buy the stock so I'll
00:04:42.479 write buy and quantity so I'll write
00:04:44.940 total quantity so I I can write it total
00:04:47.400 quantity equal to one or I can only
00:04:49.680 write one that should also work so let's
00:04:51.840 only write one for now
00:04:54.860 so after making the order class I have
00:04:57.540 to call a function that is place order
00:05:00.419 in the place order I have to specify do
00:05:02.400 thing one is the order class order
00:05:04.620 object and the second is the contract
00:05:06.419 object so you can see first I have to
00:05:07.680 send contract then order so let's send
00:05:09.780 contract first
00:05:11.639 then I'll send this Ord
00:05:14.280 that's it so whatever argument whatever
00:05:17.880 this function will give me back let's
00:05:20.340 save it in a variable called as trade
00:05:25.259 and I'll just print the trade
00:05:29.100 okay now before running the code I want
00:05:31.620 to show you one more interesting thing
00:05:32.940 what I'll do I'll write IB dot sleep
00:05:36.300 so I'll wait for one second okay after
00:05:38.639 waiting for one second again I'm going
00:05:40.199 to print the trade
00:05:42.300 okay so you'll see the difference now
00:05:44.880 when this trade will be printed and when
00:05:47.400 this trade will be printed both of them
00:05:49.139 will be giving me different answer
00:05:51.120 okay so let me first run the code and
00:05:53.220 show you so what will happen the moment
00:05:54.479 I run the code the order will be placed
00:05:56.100 and since it's a market order it will be
00:05:58.080 filled instantly
00:06:00.240 so you see the order is filled and I've
00:06:02.699 got both the output so let me just copy
00:06:05.220 both the trade so this is the first
00:06:06.840 trade that I have got so I'll just copy
00:06:08.699 it
00:06:12.000 this is the first thing I've got
00:06:14.160 and this is the second trade that I've
00:06:16.320 got
00:06:21.539 so always remember that whenever you
00:06:23.460 place a trade
00:06:24.600 in return you get order type of object
00:06:27.120 okay this is the order object that I
00:06:28.979 have got which is made out of class
00:06:30.360 trade okay and this is also the same
00:06:33.479 type but if you look at the both the
00:06:36.840 object you'll see the difference
00:06:38.639 see this the upper object ends here and
00:06:42.300 this new object which is printed after
00:06:44.699 one second has lot more data as compared
00:06:47.880 to the first trade now why is that the
00:06:50.580 case this is because whenever you place
00:06:53.039 an order it takes few second to for the
00:06:56.759 trade to be executed and to be filled
00:06:58.620 okay so if we wait for one second what
00:07:01.500 happens the trade that we are printing
00:07:04.319 is a filled trade but when we print
00:07:06.600 directly so this straight is not filled
00:07:09.060 that's the difference so in line 13 the
00:07:11.639 trade that you are printing is uh
00:07:14.819 you know in process trade that is it is
00:07:17.460 not filled yet whereas on line 15 this
00:07:20.580 trade is actually filled okay that's the
00:07:22.860 major difference so let me show you uh a
00:07:25.620 little bit more thing about both the
00:07:28.020 data that we have received so what I
00:07:29.940 will do I'll just show you all the
00:07:33.060 different data that we have in the trade
00:07:34.680 type okay so in the first first I have
00:07:36.900 contract okay so in the trade object the
00:07:39.599 first attribute that I have is contract
00:07:41.400 after contract if I go right
00:07:45.180 you will say the second attribute is
00:07:47.580 order okay so I'll go right you can see
00:07:50.400 the third attribute is order status
00:07:52.560 so you can see in the order status it is
00:07:54.479 pending submit it means it is not filled
00:07:57.000 yet and if I go right
00:07:59.699 you'll see there is this attribute which
00:08:02.520 is a list fills fills list I have then
00:08:05.759 another attribute I have that is log
00:08:08.220 okay so these are all the attributes
00:08:10.319 that I have in this trade object okay
00:08:12.720 now let me show you the different
00:08:14.759 attribute that I have in this trade
00:08:16.860 object so the attributes would be the
00:08:18.900 same okay but the difference will be
00:08:21.419 uh that the data in that attribute will
00:08:23.819 be a little bit more in the second trade
00:08:26.039 as compared to the first trade so first
00:08:28.560 I have contract if I go right again I'll
00:08:31.620 find the order
00:08:33.719 if I go right again I'll find the order
00:08:36.240 status now you see the difference here
00:08:38.399 the status for spending submit and here
00:08:40.979 the status is filled that's the major
00:08:42.659 difference
00:08:43.860 and if I go right
00:08:46.020 you'll see that this fills also in this
00:08:48.720 within this fills I have different
00:08:50.040 element within that list okay there are
00:08:52.740 lots of thing in this field
00:08:54.540 like first I have this fill type of
00:08:57.420 object if I go right then I'll find
00:09:00.300 another object that is of type execution
00:09:03.240 okay if I go right I have some basic
00:09:06.899 information like account number exchange
00:09:08.700 everything
00:09:10.440 if I go right more
00:09:12.420 I also have a object of commission
00:09:15.300 report
00:09:17.279 if I go right I have an object of time
00:09:20.760 okay so I'll not press enter for this
00:09:23.640 then at last I have object of type log
00:09:27.959 okay so that's the major difference in
00:09:30.660 this trade since the order is pending
00:09:32.640 submit it means it is not filled yet so
00:09:34.440 I only have this much of data whereas if
00:09:36.660 the order is filled so I have these many
00:09:38.959 attributes in the object okay so few
00:09:42.360 important thing you should remember that
00:09:44.760 is whenever we look at this contract
00:09:47.339 this contract will be same okay the same
00:09:49.560 contract that we have sent so you can
00:09:51.720 see we have all the data like contact ID
00:09:54.600 there was a contract ID now each
00:09:57.000 contract in IB broker has a unique ID so
00:10:00.300 for TCS the ID will be different for
00:10:02.279 Infosys ID will be different if you go
00:10:04.440 for some option contract you know like
00:10:06.060 let's say January 31st uh to 2003 2020
00:10:10.740 uh strike price call uh contract so if
00:10:14.580 you're talking about that contact that
00:10:15.839 contract will be having a unique
00:10:17.220 contract ID so for each contract the
00:10:19.320 contract ID is unique okay it won't be
00:10:21.600 same
00:10:22.680 and if you look at this Market order
00:10:24.720 you'll see that the order ID is one
00:10:27.360 argument okay now this is a very
00:10:29.399 important argument which we will discuss
00:10:31.380 in few minutes for now just notice that
00:10:34.560 both this and this are having the same
00:10:36.899 order ID because they are the same trade
00:10:38.760 this trade was taken one second like
00:10:41.339 instantly after the order was placed
00:10:42.959 this trade was noticed after one second
00:10:45.600 okay once one second has passed then I
00:10:48.000 have printed this trade
00:10:49.620 okay so what's the difference this is a
00:10:51.720 pending submit trade and this is a order
00:10:53.399 filtrate but both of them are the same
00:10:55.620 thing
00:10:56.700 now what else we have you can see if I
00:10:59.399 go right
00:11:01.019 one very informing one very important
00:11:03.120 information that is order status in
00:11:05.640 order status you can see the field and
00:11:07.740 you can also find the price at what
00:11:09.660 price this trade was filled so at 2736
00:11:13.320 price this trade was filled
00:11:16.440 Okay so
00:11:18.480 from my experience these are the only
00:11:20.519 information that are important but if
00:11:22.260 you
00:11:23.040 explore the other attribute that we have
00:11:25.740 like this fills in fields we have fill
00:11:27.839 type of object in fill type of object
00:11:30.060 again we have the contract again we have
00:11:32.459 the execution okay in execution you have
00:11:34.620 execution ID then you have time so lots
00:11:37.620 of data are available you know like we
00:11:40.140 have account number we have exchange so
00:11:42.060 lots of things are there but uh you know
00:11:44.579 from my experience they are not that
00:11:46.200 important so you know there is no point
00:11:48.540 in discussing about them
00:11:50.220 now there is also log entry so if you
00:11:52.800 see whatever trade was taken the entire
00:11:55.680 trade log entry is provided in this log
00:11:58.620 attribute so if you scroll down at what
00:12:00.660 time what happened everything is
00:12:02.279 specified in this log entry so it's
00:12:04.140 quite long okay so you can actually try
00:12:07.079 to understand it but uh it's not that
00:12:10.200 important for the sake of building algo
00:12:13.680 so I hope this is clear all right so let
00:12:15.839 me just revise it one more time so first
00:12:18.180 we have to make a contract object okay
00:12:20.760 you can make a contact object either by
00:12:22.740 using uh the function the classes
00:12:25.680 provided by IB Instinct that is stock
00:12:28.160 option future those uh those classes you
00:12:31.860 can use or you can also use the contract
00:12:33.959 class in contract class you have to
00:12:35.579 specify all the things like the exchange
00:12:37.560 the currency all those things then make
00:12:40.680 sure that you qualify the contract to
00:12:42.120 see if the contract is valid or not then
00:12:45.000 you will make a order type of object
00:12:48.180 now when it comes to making order type
00:12:49.920 of object there are two ways one is
00:12:51.660 either you can use IB in sync classes so
00:12:54.600 there are two classes provided one is
00:12:56.399 Market order and one is limit order or
00:12:58.860 you can use the original order class
00:13:02.639 okay anyone you can use make an order
00:13:04.440 object then just call the IB dot place
00:13:06.600 order function first you have to send
00:13:08.160 the contract then you have to send the
00:13:09.779 order object both object you have to
00:13:11.940 send in this function and then this
00:13:15.120 place order function will give you a
00:13:17.040 trade type of object okay now this trade
00:13:19.139 type of object if you print instantly it
00:13:21.540 will be pending submit but if you print
00:13:23.639 it after few second if the order is
00:13:26.160 filled okay if it is not filled let's
00:13:27.899 say you have placed the limit order so
00:13:29.639 the order won't be filled instantly so
00:13:31.680 even after even if you wait for one
00:13:33.480 second and if you print it the both the
00:13:36.120 trade will be same Okay the reason why I
00:13:38.639 am seeing this as a different
00:13:41.399 you know the reason why I'm saying
00:13:43.079 different attribute in this trade is
00:13:45.600 because this trade is filled okay that's
00:13:47.339 the only reason okay
00:13:49.680 so I hope this is clear now let's use
00:13:52.380 the order object okay so if I'm using
00:13:54.660 the official order object so this is how
00:13:57.000 I'll do it I'll write order
00:13:59.339 then I have to specify a very important
00:14:01.620 argument that is order ID okay so I'll
00:14:03.959 write order ID is equal to now this
00:14:06.120 number you can have whatever you want
00:14:08.040 any random number you can have let's say
00:14:09.720 right now I'm having 55. so if I have
00:14:11.940 order ID as 55 so here also order ID
00:14:14.459 will be 55 and here also it will be 55.
00:14:17.040 okay any random number you can have so
00:14:18.839 let's have some more thing like uh let's
00:14:21.899 have
00:14:23.220 four or five okay this is the first
00:14:25.260 argument then you have to specify uh the
00:14:28.860 type order type so I'll write order type
00:14:31.200 is equal to it's a market order so I'll
00:14:33.480 write MKT
00:14:35.160 okay then I have to specify total
00:14:38.160 quantity total quantity is I want one
00:14:40.620 and then I have to specify the action
00:14:42.839 that is is it a Buy trade or a sell
00:14:44.699 trade so let's do a buy so I'll write
00:14:47.040 action
00:14:48.120 is equal to
00:14:49.740 buy now if you notice in this order
00:14:52.139 object there are a lot more other
00:14:53.639 arguments you know that we can send but
00:14:56.579 for placing a basic Market order these
00:14:59.279 are the important argument you have to
00:15:01.260 send
00:15:02.339 so now if I run the code the output will
00:15:04.740 again be the same okay but the order ID
00:15:07.500 will be different in this case the order
00:15:09.240 ID will be different both the order ID
00:15:10.740 will be same but they won't be this
00:15:12.480 number it would be 555 so let me just
00:15:14.820 show you I'll just comment
00:15:16.860 this code out
00:15:24.060 okay so I've commented the code so I'll
00:15:25.560 run the code
00:15:27.360 or a field so you can see again I've got
00:15:30.300 a similar type of output so if I show
00:15:32.699 you here this is the first trade that I
00:15:34.920 have got not this this is the first
00:15:37.320 trade
00:15:38.279 okay and look at the order ID
00:15:41.880 if you look at the order ID this is 555
00:15:44.760 you can see this is the order ID and
00:15:47.040 this is the second trade I have got in
00:15:48.720 this trade the order is filled if you
00:15:50.220 look at the order status you can see it
00:15:51.839 is filled
00:15:53.100 whereas here if you see order status it
00:15:55.860 is pending submit
00:15:57.660 okay and the order ID is same here also
00:15:59.880 it is 555 here also it is 555 so this is
00:16:02.699 a long number that I was talking about
00:16:04.019 it was not a order ID it was a contract
00:16:05.760 ID okay so don't get confused
00:16:08.940 so this is how you place a basic Market
00:16:11.399 order okay so now let me show you how
00:16:13.560 you can place a limit order again there
00:16:15.300 are two ways either I can use the same
00:16:16.920 order uh order class or I can use the
00:16:20.160 limit order class that is provided by
00:16:22.680 ibnc so let me first Show You by placing
00:16:25.019 a limit order by using order type of
00:16:27.720 class
00:16:28.980 so first thing is I need to change the
00:16:31.740 order ID okay now whenever you place a
00:16:33.839 new order it should not have the same
00:16:35.220 order ID as the previous one so you can
00:16:37.440 have any number but make sure that it is
00:16:39.180 not the same so let's have 556 okay 5556
00:16:43.320 and it is a limit order so I'll write
00:16:45.720 LMT then quantities again one again I
00:16:49.079 want to buy now if it's a limit order I
00:16:51.600 have to specify it what price I want to
00:16:53.220 buy the stock okay so I have to provide
00:16:55.560 limit price
00:17:07.140 so you can see there is an argument that
00:17:09.240 is limit price now this trade was filled
00:17:14.220 at what price so if I scroll down
00:17:17.280 if you see here the fill price was 2736.
00:17:22.619 okay this was the filter price so what I
00:17:25.140 will do
00:17:26.699 I'll copy the same number now
00:17:29.580 there are two options for me that are
00:17:32.640 available one is either I can have a
00:17:34.620 price
00:17:35.760 uh you know greater than this price that
00:17:38.100 is more than 2736 or a price lower than
00:17:41.340 2736 now what will happen if I have uh
00:17:45.240 you know a greater price
00:17:47.100 so right now Market is ready to you know
00:17:51.840 uh sell this stock at 2736 and I'm a
00:17:55.080 buyer okay if I want to buy this stock I
00:17:56.760 should get the best price that is I
00:17:58.200 should get a price that is lower than
00:18:00.059 the market price okay so if I write a
00:18:03.720 price if I specify a price Which is
00:18:05.460 higher than the market price then my
00:18:07.559 order will be filled instantly okay but
00:18:10.020 if I have a price lower than the market
00:18:11.640 price then my order won't be filled
00:18:13.980 instantly okay my order will wait till
00:18:16.440 the market reaches my price once it
00:18:18.960 reaches my price that is lower than the
00:18:21.000 current market market price only then my
00:18:23.340 order will be filled right so what I'll
00:18:25.679 do right now what is the price that
00:18:27.179 let's just check it out right now
00:18:29.700 if I go to favorite and if I check
00:18:32.280 Reliance it is two three six five okay
00:18:35.280 here I have written two wait let me
00:18:37.620 check it one more time
00:18:39.179 Alliance is two three six five
00:18:42.660 and here it is
00:18:44.760 oh no we are talking about HDFC right so
00:18:47.280 HDFC
00:18:49.220 2737-2736 so if I have a number like two
00:18:52.020 seven three eight now this order will be
00:18:55.200 filled instantly because this is you
00:18:57.120 know more than the market price so let
00:18:58.919 me show you by placing the trade
00:19:01.620 so it should be filled instantly within
00:19:03.480 the one second you see it is filled
00:19:05.160 okay but what if I have a price which is
00:19:08.280 lower than the market let's say I have
00:19:09.900 three one three two okay now this won't
00:19:13.020 be filled instantly my order will wait
00:19:15.539 till the market reaches my point once it
00:19:18.240 reaches my point that is my price only
00:19:20.460 then the order will be filled so let me
00:19:22.140 show you if I run the code you'll see
00:19:24.480 you will not see any order filled uh
00:19:26.700 notification here if I go here you can
00:19:29.100 see if I go to order
00:19:31.320 and if I scroll
00:19:33.480 up and down if I click on live order you
00:19:37.799 can see the TCS order right now
00:19:45.620 okay wait let me just cancel this
00:19:53.400 I'll just show you here
00:19:56.100 so you should see
00:19:58.500 okay it is showing an error
00:20:02.280 stock this trade this
00:20:05.880 and it you can see error 104 cannot
00:20:09.299 modify a okay now I have made a very
00:20:12.740 uh important I can say or I can say a
00:20:15.840 very crucial mistake and what was that
00:20:17.760 mistake I try running the same code
00:20:20.640 twice okay and I didn't change my order
00:20:22.679 ID that's why it wrote an error so
00:20:25.500 whenever you place a new order you have
00:20:27.419 to make sure that you use a unique order
00:20:29.640 ID if you use the same order ID that you
00:20:31.740 have used previously then it will always
00:20:33.240 throw an error so what I should do is I
00:20:36.059 should have a different number like five
00:20:37.799 five five eight now this order ID was
00:20:40.500 never used so now if I run the code it
00:20:42.660 should not throw an error
00:20:46.380 so yeah it was executed and you can see
00:20:48.500 this is a
00:20:51.000 active
00:20:52.620 order you can see here right is not
00:20:54.840 filled yet now the moment HDFC price
00:20:57.539 reaches this level that is 2732 only
00:21:00.419 then this order will be filled and if
00:21:02.820 you look at the output both the trade
00:21:04.980 are almost same this is also same and
00:21:07.380 this is also same both of them are
00:21:09.179 having the same order status that is let
00:21:11.880 me show you the order set status
00:21:15.059 so here it is pending submit and here it
00:21:18.780 is okay wait here it is not pending
00:21:20.460 submit here it is submitted okay there
00:21:22.740 is a difference after waiting for one
00:21:24.840 second first it was pending submit it
00:21:26.700 means it was not submitted but after one
00:21:28.500 second uh this order was submitted but
00:21:31.860 it is not filled yet you can see filled
00:21:33.600 it is still zero the moment it will be
00:21:35.760 filled if I run this code again if I run
00:21:38.100 this trade again then you should see
00:21:40.980 that within this field I will be getting
00:21:42.720 all the information like at what price
00:21:44.820 the order was filled and other
00:21:47.340 information
00:21:48.480 okay so I hope this is clear okay now
00:21:51.179 I'll try to place a trade by using the
00:21:54.059 limit order function so I'll write limit
00:21:56.280 order now the benefit of using a limit
00:21:58.919 order is I don't have to manually uh you
00:22:01.860 know change the order ID so whenever I
00:22:04.500 call limit order or order limit order or
00:22:07.140 Market order any type of class so those
00:22:10.140 classes automatically change the order
00:22:11.820 ID for me I don't have to manually
00:22:13.799 change any order ID so here I just have
00:22:16.020 to specify first action
00:22:18.659 so let's say I want to sell so I'll
00:22:21.059 write
00:22:22.980 sell and I want to sell
00:22:26.220 quantity so I will specify the quantity
00:22:28.320 as one and limit price at what price I
00:22:31.140 want to sell so let's say I want to sell
00:22:33.299 at
00:22:35.220 now so if I'm selling I have to quote a
00:22:37.919 price higher than the market okay so
00:22:39.960 right now it is 2734 let's try to sell
00:22:42.720 it at 2 7 3 8.
00:22:47.100 two seven three eight now this won't be
00:22:49.679 filled instantly but if I have a price
00:22:51.539 lower like if I have three one this will
00:22:54.000 be filled instantly so let me show you
00:22:55.559 so if I run this code this should be
00:22:57.419 filled instantly or filled you can see
00:22:59.280 it is filled instantly
00:23:01.380 okay so this is how you can place a
00:23:05.340 either a market order or a limit order
00:23:07.740 by using this functions or you can say
00:23:11.460 the classes provided by ID in sync
