
# tactiq.io free youtube transcript

# Real-Time Bar Data Made Easy with Interactive Brokers Python API -Part 3

# https://www.youtube.com/watch/ARKyAVQT4Vs

00:00:00.780 hi so in our previous session we have
00:00:03.720 started or I can say we have completed
00:00:06.000 the contract class so we have discussed
00:00:07.620 what's a contract class so contract
00:00:09.240 class is used to represent an instrument
00:00:12.000 so whatever stock you are dealing with
00:00:14.160 you have to make a contract of that
00:00:15.719 stock before doing anything else this is
00:00:17.940 what we have discussed and we have seen
00:00:19.680 how we can make a contract of a stock
00:00:22.760 option future so whatever uh instrument
00:00:26.039 you're dealing with you can make a
00:00:27.300 contract of that
00:00:28.500 then we have discussed about historical
00:00:30.539 data how you can get uh historical data
00:00:33.239 so we have used a function called as
00:00:34.620 request historical data function so
00:00:36.840 whenever you will call this function
00:00:38.219 this function this function will give
00:00:39.899 you
00:00:40.680 candle historical data okay ohlc data
00:00:44.160 now uh let me point out one thing in
00:00:47.520 this that is this end point end date
00:00:50.460 time argument so in this end date time
00:00:53.700 argument we can send empty string and
00:00:56.219 whenever you send an empty string it
00:00:57.780 will give you the latest candle data too
00:01:00.480 like let me give you an example let's
00:01:02.280 say that I run this code at 9 30. so if
00:01:07.619 I run this code at 9 30 I will be
00:01:09.360 getting the latest candle till 9 29 so
00:01:12.240 till 9 29 all the one minute candle
00:01:14.520 let's say I am trying to get one minute
00:01:16.560 candle okay so 929 candle
00:01:19.500 uh also I will be getting now let's say
00:01:22.080 now it is 9 30 and one second okay it's
00:01:25.500 almost 31. so once this the entire
00:01:29.939 minute is completed once we move to the
00:01:31.740 next minute then if I call this function
00:01:34.140 after the minute is over so the previous
00:01:36.840 minute data also I will be getting okay
00:01:40.619 this is the benefit of using this
00:01:42.240 function if you write an empty string
00:01:44.520 okay this is one thing you should
00:01:46.079 remember that is uh I will be getting
00:01:48.299 the latest candle data if I am writing
00:01:50.759 one minute
00:01:51.960 the moment that that candle is generated
00:01:54.299 if I call this function after that
00:01:56.520 candle is generated that candle I will
00:01:58.680 be receiving if I call this one sure
00:02:01.560 now
00:02:03.780 let's say you are making you are
00:02:05.460 designing an algo okay now there are two
00:02:07.259 things you can do in this case one is
00:02:09.300 you whenever you need
00:02:11.340 uh the data you just call this function
00:02:13.920 okay this is one approach the other
00:02:16.620 approach is to make a websocket now
00:02:18.840 what's a web socket now what is a
00:02:21.420 problem in this first method the problem
00:02:23.520 is whenever I need the data I need to
00:02:25.440 call it okay let's say I want after
00:02:28.620 every five second I want the data so I
00:02:30.959 have to call this after every five
00:02:32.340 second it's not like you cannot do it
00:02:33.840 you can do it you can put it in a for
00:02:35.520 Loop you just call it after every five
00:02:36.900 second you'll get the same result now
00:02:39.060 there is an alternative way of doing the
00:02:41.220 same thing so that way is called as a
00:02:43.379 websocket way okay so what we do we make
00:02:45.900 a connection between our python file and
00:02:48.120 the server okay so this connection is
00:02:50.160 called as web socket connection
00:02:52.019 now what's a benefit of websocket
00:02:53.700 connection in websocket connection you
00:02:55.739 don't have to make any calls okay so
00:02:57.840 there is one connection a pipeline that
00:02:59.700 is made between your file and the server
00:03:02.280 and the server will keep sending you
00:03:04.500 data after uh X interval of time okay
00:03:07.980 now this interval
00:03:09.599 in case of Interactive Broker is five
00:03:11.640 second
00:03:12.480 for after every five second it will send
00:03:15.239 a new candle data so the minimum candle
00:03:18.239 size and Interactive Broker is five
00:03:19.620 seconds after every five second you will
00:03:21.180 be receiving a five second candle data
00:03:24.000 now remember I'm saying candle data it
00:03:26.159 means I will be receiving ohlc data
00:03:28.860 okay so that is what we will be
00:03:30.659 discussing today that is how we can make
00:03:32.580 a websocket connection between our file
00:03:34.620 and the server and after every five
00:03:37.019 second how we can get real-time bar data
00:03:39.060 okay this is what we will be discussing
00:03:40.799 right now so let's make a new file
00:03:43.500 so I'll write
00:03:45.780 real
00:03:47.040 dot real bar Dot py
00:03:50.819 now whenever you are starting a new
00:03:53.340 project you can simply copy the code
00:03:55.200 that you have written in your previous
00:03:56.400 session okay so I'll just
00:03:59.159 or let's just copy everything
00:04:03.239 I'll paste it here I'll run the code and
00:04:06.239 see if it is working or not
00:04:09.780 so my Interactive Broker is also live
00:04:11.819 right now
00:04:13.980 okay you can see I've got the data now
00:04:16.320 what's the candle uh what's the stock or
00:04:19.260 the instrument that I'm dealing with I'm
00:04:20.820 dealing with Forex instrument okay and
00:04:24.120 you can see this is the latest candle
00:04:25.800 that I've received and what
00:04:27.780 candle size I'm requesting for I'm
00:04:29.880 requesting for one minute candle size so
00:04:32.400 right now it is 853 okay so if I run the
00:04:35.699 code after one minute I should also get
00:04:37.440 a 854 also after one minute if I run
00:04:40.380 this code you'll see I'll also be
00:04:41.460 getting 854 too okay so let's wait for a
00:04:44.820 few minutes I'll run it again and I'll
00:04:45.960 show you till then uh let me explain you
00:04:50.400 few other things
00:04:52.620 okay so till
00:04:55.080 you know one minute passes by I'll just
00:04:57.240 show you the documentation
00:04:58.979 so once you visit their website you know
00:05:01.680 the IB official documentation there is
00:05:03.479 one link that is very important for us
00:05:05.940 that is this notebook link
00:05:07.860 if you click on this notebook you'll see
00:05:09.479 that they have provided us with some
00:05:11.040 basic notebooks okay so these notebook
00:05:13.320 you can refer to whenever you're
00:05:14.820 building
00:05:15.900 uh strategy okay so in this right now we
00:05:19.440 will be discussing this bar data
00:05:22.800 Jupiter notebook so I'll just click on
00:05:24.840 it
00:05:26.520 so if I click on it this is the Jupiter
00:05:28.560 file that will open okay now let's see
00:05:31.080 you know we have already discussed half
00:05:32.820 of it like we have seen how we can make
00:05:35.759 a connection then how we can get the
00:05:37.620 data we can simply use the request
00:05:39.900 historical data function it will get us
00:05:41.639 the data
00:05:42.780 okay and uh yeah this is what we have
00:05:46.380 discussed now if you scroll down you'll
00:05:47.940 see uh there is this heading of Real
00:05:50.100 Time bar okay this is what we will be
00:05:51.900 discussing today so what I'll do first
00:05:53.759 I'll copy the code
00:05:55.380 so there is one function that they have
00:05:57.060 made so let's copy that function name
00:06:00.740 I think it uh one minute should be over
00:06:03.780 by now if I run the code again
00:06:05.940 see now not only 54 it is also giving me
00:06:08.460 55. so after every minute you know I get
00:06:11.400 the real-time data now let's come back
00:06:13.919 to real-time bar data so first you have
00:06:16.740 to make a function okay now this
00:06:19.080 function can you can name it whatever
00:06:21.000 you want in this case we have named it
00:06:22.919 on bar update so what will happen once
00:06:25.440 we make the websocket connection
00:06:27.539 whatever data we will be getting that
00:06:29.580 data will be stored in this bar variable
00:06:31.860 okay so if I print this bar variable it
00:06:34.680 will keep getting printed after every
00:06:36.419 five second so I'll show you in few
00:06:37.979 minutes
00:06:38.880 this is first thing then we have to copy
00:06:40.979 these two lines of code so let me just
00:06:42.600 copy this
00:06:45.539 I'll paste it here so what we have done
00:06:47.580 we have called this request Real Time
00:06:49.800 bar function okay so if you want a
00:06:53.220 normal historical data you call the
00:06:55.319 function request historical data
00:06:57.000 function if you call it request
00:06:58.500 historical data function it will give
00:06:59.880 you a historical data but if you call
00:07:02.280 request Real Time bar function okay now
00:07:05.160 this is a little different function
00:07:07.380 what this function will do this function
00:07:09.360 will create a websocket connection
00:07:10.860 between you and your server okay so we
00:07:14.699 will call this function in this way
00:07:15.960 request Real Time bar and then we will
00:07:18.000 be sending four argument okay first
00:07:20.160 argument will be the contract for which
00:07:22.080 contract we want to uh subscribe that is
00:07:25.020 for which contract we want real-time
00:07:26.580 data then 5 means after every 5 Second
00:07:29.340 we will be receiving the data and the
00:07:31.380 other two uh will remain the same okay
00:07:33.419 so you don't have to change the last
00:07:35.039 three only this contract will change
00:07:36.960 rest of the things will remain the same
00:07:38.819 okay and in the next line you have to
00:07:40.979 write this code okay you will write bars
00:07:43.020 dot update event plus equal to on bar
00:07:45.720 update now what is this on bar update on
00:07:47.639 bar update is the name of this function
00:07:49.560 I told you that this function you can
00:07:51.660 name whatever you want so in few minutes
00:07:53.280 I'll change the function name and I'll
00:07:54.599 show you but for now let it remain the
00:07:57.120 same
00:07:58.020 now if I only copy this much and if I
00:08:00.660 run the code nothing will happen so let
00:08:02.520 me show you if I run the code
00:08:05.099 uh nothing major difference will be
00:08:07.860 there
00:08:08.759 why nothing is happening because I have
00:08:11.460 made the connection but I have not
00:08:12.960 started the connection okay now if you
00:08:15.539 want to start the connection there are
00:08:16.979 two ways one is you make a infinite
00:08:20.699 connection so if you want to make an
00:08:22.199 infinite connection you just write IB
00:08:23.819 dot run
00:08:24.960 okay if I only write this if I only
00:08:26.879 write this much and if I run the code a
00:08:28.560 connection will be made and I will
00:08:30.240 receive the data for
00:08:32.880 forever okay there is no stopping this
00:08:35.219 connection this is one way so before
00:08:37.320 showing you this way I'll show you the
00:08:39.120 second way
00:08:40.260 second way is I'll just go to the
00:08:42.839 documentation again and I'll copy these
00:08:44.940 two lines of code
00:08:46.380 so what we do we specify us set time you
00:08:50.760 know like we want this connection to be
00:08:52.380 for 30 second one minute whatever it is
00:08:54.660 and we will write a sleep command Okay
00:08:57.240 in this leap Command right now that is
00:08:58.800 30 seconds so we will make a connection
00:09:00.240 for 30 second after 30 second we will
00:09:02.820 close this connection
00:09:04.380 which connection the connection between
00:09:06.120 this python file and the server
00:09:08.700 okay so let me repeat everything one
00:09:10.920 more time what what things we have done
00:09:12.720 first we have made a function this
00:09:14.339 function name you can have whatever you
00:09:16.080 want this function should have two
00:09:17.339 argument okay two arguments are also not
00:09:19.500 mandatory you can only have one argument
00:09:21.240 it should also work
00:09:22.860 then right now that argument is bars so
00:09:26.160 this also you can name whatever you want
00:09:27.959 okay it's not compulsory that you have
00:09:29.820 to Name Bar only okay two arguments are
00:09:32.760 there and whatever argument I'm getting
00:09:34.560 so let's just print it okay instead of
00:09:36.480 writing minus one I'll just print it for
00:09:38.459 now okay and then we are calling the
00:09:40.980 request Real Time bar function in this
00:09:43.440 we are sending four argument the other
00:09:45.360 three will remain the same the only
00:09:47.339 thing you have to keep in mind is the
00:09:48.959 contract so for whichever contract you
00:09:51.660 want to make a connection you have to
00:09:52.980 specify that contract here then we will
00:09:55.440 call we will write bar dot update event
00:09:58.560 okay plus equal to on bar update
00:10:01.800 Okay so
00:10:03.600 this line is going to start a connection
00:10:05.760 between your computer and
00:10:08.760 your not start is going to make a
00:10:11.640 connection okay if you wish to start the
00:10:13.380 connection you either you can write IB
00:10:15.420 dot run which will create an infinite
00:10:17.160 connection or you can use the Sleep
00:10:18.480 command okay after sleeping for 30
00:10:20.640 seconds we will cancel this connection
00:10:23.100 so what will happen if I run the code
00:10:24.899 first a connection will be made
00:10:26.459 instantly then I'll start receiving data
00:10:28.620 after every five second okay in the
00:10:30.660 first second I'll get one data after
00:10:32.399 five seconds again I will be receiving
00:10:33.959 the data so let's run the code and see
00:10:36.480 first I am getting the historical data
00:10:38.160 now I've got the data and after five
00:10:39.779 seconds I'll get another data
00:10:43.200 see again I've got the data now this is
00:10:45.779 so fast that it is not visible properly
00:10:47.700 so what I will do I'll just convert it
00:10:49.500 into a data frame okay so how do you
00:10:51.600 convert something into a data frame if
00:10:53.160 you remember you we use the util.df
00:10:55.140 function
00:10:56.100 I'll write DF is equal to
00:10:59.399 util dot DF we will send this bars in
00:11:03.600 this
00:11:04.380 and we will print this DF
00:11:07.820 so let's just remove this bar for now or
00:11:11.100 let's just comment it and I'll run the
00:11:12.839 code again now instead of showing the
00:11:14.700 raw data it is going to show the data in
00:11:16.500 a data frame format so see after every
00:11:19.920 five second I'm receiving a new data so
00:11:22.620 here there was only one data so let me
00:11:25.320 just scroll up here there was one data
00:11:26.940 then two data then three data then four
00:11:30.060 data okay then finally five data so you
00:11:33.360 can see the difference also there is a
00:11:34.740 five second Gap 15 20 25 30 35 40. so
00:11:39.420 after every five second I'm receiving a
00:11:41.880 new candle data and the size of that
00:11:43.920 candle is 5 Second so this ohlc is First
00:11:47.160 5 Second
00:11:48.300 okay so I hope this is clear
00:11:50.700 so this is how you make a connection
00:11:52.140 between your computer and the server by
00:11:55.500 using the websocket now since we have
00:11:57.300 written 30 seconds so we only got six to
00:11:59.519 seven candle
00:12:00.779 okay now I'll show you the other way
00:12:03.420 that is instead of using the Sleep
00:12:05.579 command I'll directly write IB dot run
00:12:08.700 so what this will do this is going to
00:12:10.500 make a connection forever and there is
00:12:13.079 no way to stop this connection there is
00:12:14.579 only one way that is to close the
00:12:15.899 terminal so once I run the code so I'll
00:12:18.120 just run the code and show you it will
00:12:20.279 start the connection it will start
00:12:21.600 sending me the data okay but if I want
00:12:24.480 to close it I just have to click on this
00:12:26.700 Del button because I have not written
00:12:28.380 the code to stop this connection so you
00:12:31.800 can see after five second right now it
00:12:33.360 is 35 now I'll get 40 also I've got 40
00:12:35.760 then I'll get 45 also so in this way uh
00:12:39.300 each time it will send a new data
00:12:42.120 it's going to also send me the older
00:12:44.100 data too okay like let me give you an
00:12:46.560 example let's say that I have started
00:12:48.180 this connection at 9 15. okay so at 9 15
00:12:52.380 I will be receiving one candle then the
00:12:54.899 next candle I will be receiving at 9 15
00:12:57.120 5 Second
00:12:58.440 okay now in the next call at 9 10 9 15
00:13:02.940 minute 10 second I will be receiving two
00:13:05.459 candle the first candle also second
00:13:07.200 candle also now at 9 15 15 second there
00:13:10.860 will be three candle so I won't be
00:13:12.420 receiving only single candle from the
00:13:14.040 server I will be receiving all the three
00:13:15.779 candle uh in the call so as the time
00:13:19.620 progresses
00:13:20.880 whatever candle we are receiving will
00:13:23.579 keep getting accumulated
00:13:25.440 okay so this is something you should
00:13:27.000 understand so if you have not understood
00:13:28.380 I'll repeat it one more time so whenever
00:13:30.540 you start a connection
00:13:32.040 once that minimum time frame that is 5
00:13:35.639 Second is completed
00:13:38.100 when we move to the next candle so not
00:13:40.680 only the current candle but also the
00:13:42.480 previous candle
00:13:44.040 uh is being sent via websocket
00:13:48.360 okay like let's say there is 60 seconds
00:13:50.519 are done so in 60 seconds there will be
00:13:52.800 total or 12 candle will be formed so I
00:13:55.980 won't be receiving only the latest
00:13:57.240 candle but I will be receiving all the
00:13:59.279 12 candle uh in each request in each
00:14:02.820 response okay so I hope this is also
00:14:05.339 clear
00:14:06.180 so this is how you make a websocket
00:14:08.760 connection now let's do few more changes
00:14:10.680 so I'll not use this IB dot run for now
00:14:12.959 let's use the 30 second
00:14:15.839 now let me just change the name okay
00:14:17.639 instead of on bar I can name whatever I
00:14:19.980 want like maybe enough Professor Pro 1.
00:14:22.920 and here I'll write
00:14:24.540 I have to write the same function name
00:14:26.279 so if I run the code again again it
00:14:27.899 should work in the similar fashion
00:14:29.279 nothing will change
00:14:32.220 you can see it is working similarly now
00:14:34.860 let's see if I only send one data what
00:14:37.740 will happen so right now I'm sending
00:14:39.540 bars right so I can change this also so
00:14:41.940 let's say instead of bar I'll just write
00:14:43.560 my name Sunil and here I have to specify
00:14:46.260 Sunil
00:14:47.459 and that's it
00:14:49.320 okay so if I run the code
00:14:51.000 again it should give me the same data
00:14:53.399 now let's just remove the second
00:14:54.899 argument and see if it works in a
00:14:57.540 similar way or not
00:15:03.480 so it is not working in this case so I
00:15:05.760 need to sign to argument so this two
00:15:08.339 argument you need to have in this
00:15:09.660 function this is something you should
00:15:10.860 keep in mind so I'll just close it
00:15:13.620 now instead of printing it this way okay
00:15:16.740 let me just print the bar
00:15:19.199 okay I'm just printing the bar that is
00:15:21.480 I'm just painting The Raw data not the
00:15:23.699 entire data frame but instead of
00:15:25.860 printing the data from let's print the
00:15:27.240 raw data and I'll show you some some
00:15:30.120 interesting thing
00:15:31.680 okay so what I'll do I'll just copy this
00:15:35.339 data so let me just copy this
00:15:40.440 okay so I've copied few data and I'll
00:15:43.800 just paste it and let's try to analyze
00:15:46.079 the data
00:15:47.100 okay first of all this is that list that
00:15:50.160 I have received when
00:15:52.139 uh this is the first data that I have
00:15:54.120 received when I started the connection
00:15:55.440 then after the first this is the second
00:15:57.899 data that I've received so whenever I'm
00:16:00.060 receiving the data I'm getting it in a
00:16:01.680 list format okay and in the list I have
00:16:04.260 this object Real Time bar so Real Time
00:16:06.360 bar is an object of a Class Real Time
00:16:09.060 bar so till now we have seen two classes
00:16:11.279 okay one is contract class and one is a
00:16:14.459 request historical data class Okay so
00:16:17.760 I'll also show you
00:16:19.560 what type of data we are getting when we
00:16:21.720 call the request historical data
00:16:23.160 function okay so here you can see we are
00:16:25.380 converting into a data frame along with
00:16:28.019 before converting into a data from let
00:16:30.000 me just print the raw data too okay to
00:16:32.279 show you uh what's the class name of
00:16:34.380 this bar type
00:16:35.579 okay so I am printing the bars here and
00:16:38.759 then I'm converting into a data frame
00:16:40.380 and here I've already copied this data
00:16:44.040 okay so let's run the code
00:16:48.440 I'll just copy something
00:17:01.880 okay so I've copied the data
00:17:05.040 I'll just paste it here
00:17:10.079 okay so let me repeat it one more time
00:17:12.359 what are these two data so this data I'm
00:17:14.640 getting from a websocket okay first time
00:17:17.579 I received this
00:17:18.959 in the second in the second response I
00:17:21.419 received this
00:17:22.500 now what is this data this is the data
00:17:24.599 that I've received when I call this
00:17:26.640 function that is request historical data
00:17:28.319 function so whenever I call request
00:17:29.700 historical data so I received this type
00:17:31.919 of data and just look at the name of the
00:17:34.380 object so here it is Real Time bar it's
00:17:36.900 the object of the Class Real Time bar
00:17:38.700 and here it's an object of bar data so
00:17:41.820 this object was formed from a class with
00:17:44.760 the name bar data okay this is the basic
00:17:47.340 stuff that you should understand okay
00:17:50.760 so what we can note from this we can
00:17:54.000 note that whenever you use the request
00:17:56.520 historical data we get a different class
00:17:58.500 and that class name is bar data class
00:18:00.299 and whenever we call whenever we call
00:18:03.720 this request Real Time bar function we
00:18:07.260 get real time bar data
00:18:10.080 okay it's a very important information
00:18:11.700 because in future when we will be using
00:18:14.100 different function different function
00:18:15.419 will be giving me different types of
00:18:17.280 object okay so this is something you
00:18:20.460 should understand if you're not
00:18:21.480 understanding this I'll request you to
00:18:22.799 watch it again
00:18:24.059 now let's see what things we have in
00:18:26.640 this real-time bar data so if I go to
00:18:28.980 the right side first I have this time
00:18:31.919 okay after time I have time zone this is
00:18:36.000 the Zone time zone then I have open high
00:18:39.720 low close
00:18:41.460 okay then I have volume then count all
00:18:44.400 these things are there now in the first
00:18:47.039 response I only have one data but in the
00:18:49.860 second response I have two data you can
00:18:51.960 see comma there is a two data within the
00:18:53.520 list in the third response I will be
00:18:55.500 getting three data
00:18:56.940 okay what will be the type of the data
00:18:58.980 type will be real time bar type
00:19:01.980 okay so what this function if you
00:19:04.860 remember this util.df function is doing
00:19:07.380 this is taking this list and it is
00:19:09.600 simply converting it to a data frame
00:19:11.220 that's what this util.df function is
00:19:13.200 doing
00:19:13.860 similarly here also the same thing is
00:19:15.900 happening so we are getting a list of
00:19:18.179 bar data okay there are multiple in a
00:19:21.240 single list there are multiple bar data
00:19:23.100 type of data and this util.df function
00:19:26.520 is converting that list into a data
00:19:28.320 frame
00:19:30.000 okay
00:19:31.140 all right so let's see what what things
00:19:34.559 we have in bar data too so first we have
00:19:37.380 the date whatever date it is then open
00:19:40.559 high low close volume average
00:19:43.679 okay then the next bar data is there
00:19:45.840 okay so these are the basic data that we
00:19:48.539 get when we call the Real Time bar
00:19:51.660 function and the bar data function
00:19:54.539 I hope this is also clear so let me just
00:19:56.520 remove these two things or I'll I can
00:19:58.500 just comment it out for now so whenever
00:20:01.020 you are using any function just try to
00:20:03.960 analyze what data you are getting okay
00:20:05.940 what's the function name what are the
00:20:07.559 different things that are there in that
00:20:08.940 function okay because see since there
00:20:11.460 are these many things so when I convert
00:20:12.900 it into a data frame
00:20:14.400 even at that time these are the column
00:20:16.620 names so if I run the code again I'll
00:20:19.200 just comment the code first let me
00:20:20.880 comment this
00:20:22.500 and here also I'll comment this
00:20:25.500 because I don't want to print the raw
00:20:27.660 data I'll print the DF data now I'll
00:20:30.780 just show you if I run the code whatever
00:20:33.780 argument you are seeing here you know
00:20:35.640 like this date then you can see open
00:20:39.059 hello close what are these These are
00:20:40.559 nothing but the name of the column you
00:20:42.720 see first that is time then end time
00:20:44.520 open high low close these are the column
00:20:46.740 names that we get
00:20:49.140 okay from where we are getting this
00:20:50.640 column name we are getting it from all
00:20:53.100 the data that we have within that object
00:21:00.600 all right
00:21:02.100 so this was about how we can make a
00:21:04.440 websocket and how we can get real-time
00:21:06.539 bar data
00:21:14.460 so before moving to the next class let's
00:21:16.620 see if you're more thing about this both
00:21:19.140 the function that is request historical
00:21:21.000 data function not function the class and
00:21:23.100 the request Real Time bar plus
00:21:26.580 now about the request historical data
00:21:29.700 function
00:21:31.440 in this we were specifying the end date
00:21:34.080 time as an empty string okay what if I
00:21:37.320 specify a particular date you know like
00:21:39.480 maybe I'll specify 2011. so what it will
00:21:42.179 do if I specify 2011 so from that day to
00:21:47.640 100 days back so if I write here 100 day
00:21:51.120 okay so from that day till 100 day back
00:21:54.059 all the days data I will be getting
00:21:57.360 okay so for those of you who are
00:21:59.220 wondering how can we get lots of data
00:22:01.679 you know like I want 10 years of 4X data
00:22:04.260 so how will you do that now it's not a
00:22:06.960 good idea to directly specify uh 10
00:22:09.900 years one minute data if you do in this
00:22:12.240 way then it is not going to work because
00:22:14.159 what this API will do this API will try
00:22:17.039 to fetch the entire data in one go and
00:22:19.740 that will be a huge data right there
00:22:22.679 will be like millions of columns okay so
00:22:25.740 if you try to fetch this entire 10 years
00:22:28.260 of data in one request call in one call
00:22:31.020 then mostly it is not going to go
00:22:33.240 through okay you will not get the data
00:22:35.100 so how do we solve this problem okay so
00:22:37.620 this itself is a problem right A lot of
00:22:40.980 people search a lot about this how we
00:22:43.500 can get 10 years of data 20 years of
00:22:45.720 data historical data so I want you guys
00:22:48.780 to give it a try okay I'm not going to
00:22:50.640 explain it right now later in the future
00:22:52.919 part of our course I'll explain you how
00:22:55.440 we can solve this problem of getting you
00:22:58.320 know maybe five year 10 years of data
00:23:01.200 so one hint I'll give you if I Chi if
00:23:03.780 you just change this end date time
00:23:05.760 okay if you change this end date time
00:23:07.320 you can get historical data also but the
00:23:09.600 problem is you can only get a limited
00:23:11.940 time period of data like 100 day of data
00:23:14.760 Maybe 200 data 200 days of data you can
00:23:17.520 fetch at a time you cannot fetch the
00:23:19.980 entire data in single go that is not
00:23:21.720 going to work properly
00:23:23.640 all right so I want you guys to solve
00:23:25.500 this problem okay I will be discussing
00:23:27.360 this a later part of our course this is
00:23:29.280 one thing about this
00:23:30.659 and as far as the request real-time bar
00:23:33.000 data is concerned let's try some other
00:23:35.159 stock okay so right now I was using the
00:23:38.159 Forex Forex instrument but what if I use
00:23:41.520 some other instrument
00:23:42.900 okay like we can take
00:23:46.380 so right now uh other markets are open
00:23:49.500 but the problem is I don't have any
00:23:52.260 valid data subscription for us
00:23:55.200 stocks so if I try getting real-time
00:23:58.140 data for U.S stock it might not work
00:24:00.299 okay for few stock it might work but
00:24:03.059 most of the stock will not work for this
00:24:06.120 account so if you want us real time
00:24:09.960 stock data then you need to subscribe
00:24:12.720 for their subscription so they have some
00:24:14.520 subscription fee per month so if you pay
00:24:16.440 that data or if you pay that money then
00:24:19.620 you will be able to get the real-time
00:24:21.419 data so let's just try one of the stock
00:24:23.159 I don't think it will work but we can
00:24:24.720 try it let's try Google stock
00:24:27.000 so what stuff I need to change
00:24:30.720 foreign
00:24:32.400 this
00:24:37.020 it can remove the comments from here
00:24:40.200 instead of option
00:24:43.260 okay I'll just comment this also
00:24:47.340 we we will uh we will try this example
00:24:50.460 too so let's make a new
00:24:53.520 contract all together so I'll write C is
00:24:55.740 equal to
00:24:58.799 I'll write stock
00:25:05.280 symbol will be
00:25:08.700 Google
00:25:13.140 exchange will be
00:25:16.320 NYSE
00:25:18.840 and currency will be
00:25:22.919 USD
00:25:25.740 okay this should be good enough so let's
00:25:28.080 see if this works or not so let's run
00:25:30.720 the code
00:25:36.380 so you can see it is not working because
00:25:38.760 I don't have any active data
00:25:40.740 subscription right now so in case if you
00:25:43.740 see the similar type see you can look at
00:25:45.539 the error to it is saying the requested
00:25:46.980 Market data is not subscribed which
00:25:49.020 means I don't have the data subscription
00:25:52.260 now I do have the Indian market data
00:25:54.900 subscription but the problem is the
00:25:56.279 market is closed right now okay right
00:25:57.779 now it is 6 47 pm and right now Indian
00:26:00.299 market is not open so if I try to fetch
00:26:03.299 any real-time data for Indian stock that
00:26:05.820 is also not going to work so let me just
00:26:07.559 show you
00:26:08.880 so I'll just comment this out
00:26:11.539 and I'll uncomment this so line 9 on
00:26:14.880 line nine I'm having an option contract
00:26:17.400 okay so let's see if this works so I
00:26:20.400 will be able to fetch the historical
00:26:21.900 data okay but I won't be able to fetch
00:26:25.500 the real-time data
00:26:28.500 so let's see if I'm able to get the
00:26:30.179 historical data
00:26:32.460 so always remember that whenever you are
00:26:34.380 using this Real Time bar
00:26:36.360 uh function the market should be open if
00:26:39.840 the market is closed then you know this
00:26:42.360 function this websocket connection is
00:26:44.159 not going to work because this websocket
00:26:45.600 connection only works when the market is
00:26:47.279 open
00:26:51.080 okay see the reason why it is taking so
00:26:53.760 much time is because I am fetching one
00:26:55.860 minute data for 100 days this is going
00:26:58.380 to take a lot of time
00:27:00.240 so instead of uh 100 day let me just
00:27:04.140 write one day one day one minute data it
00:27:06.960 should be able to fetch pretty fast
00:27:23.100 so you can see I've got the data I've
00:27:25.260 got the latest data 1529 whatever the
00:27:27.779 price of the stock was at that time
00:27:30.539 so yeah I guess that's it for the Real
00:27:33.779 Time bar function
00:27:35.940 a real-time bar class and the historical
00:27:38.940 or you can say the request historical
00:27:41.880 data class these are the two classes
00:27:43.559 that we have discussed one request
00:27:45.659 historical data class is used to get
00:27:47.340 historical data and request real-time
00:27:49.740 bar data is used to get a websocket
00:27:52.200 connection and get real-time bar data
00:27:54.539 after every five seconds
00:27:56.159 now
00:27:57.179 you have to understand that here we are
00:27:58.919 getting the bar data that is we are
00:28:00.539 getting ohlc data after every second we
00:28:02.760 are not getting tick level data so the
00:28:04.559 stick level data we will be discussing
00:28:06.120 in our next session okay what is stick
00:28:07.980 level data and how do we get the tick
00:28:09.779 level data
00:28:11.279 foreign
