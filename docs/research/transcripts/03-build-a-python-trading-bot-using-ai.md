
# tactiq.io free youtube transcript

# No title found

# https://www.youtube.com/watch/J3VEniAKg5A

00:00:00.000 No text
00:00:00.160 in this video we're going to build a very simple algorithmic trading bot that we are going to use to make an automated
00:00:07.600 trading strategy in a paper trading account now I would be lying if I said
00:00:12.960 "Hey guys I found a way to print money and I'm going to just share it freely on the internet." And I wouldn't really
00:00:19.119 believe anyone that says something like that so what we're doing in this video
00:00:24.320 is just making a basic strategy that I have not confirmed at all whether it
00:00:31.119 would actually work to generate profit just as a proof of concept that we can build a bot get it to implement the
00:00:37.200 rules that we want it to implement and execute the trades that we want it to execute and then what I'll probably do
00:00:43.520 based on what I did here is you know offline off of the videos try to test out some different rules and see if I
00:00:49.840 can actually find anything that really does work and you can bet if I do find something that really does work and
00:00:55.120 generates a ton of money i will not be sharing it freely on the internet I will be living on my own island at that point
00:01:00.000 No text
00:01:01.440 if you want to follow along with me in this tutorial you should go ahead and click the link in the description that
00:01:07.600 says to sign up for datalure so that'll take you to this page right here and
00:01:13.119 you're going to see an option that says uh cloud free get started for free so
00:01:19.439 feel free to click on that and then just sign up and then once you've signed up you're going to see a page that looks a
00:01:26.560 little bit like this what you can do here is either create your own notebook or you can just go to the link in the
00:01:30.000 No text
00:01:33.520 description of the video and then click on the link that's going to allow you to download a copy of the file that I'll be
00:01:40.400 using for this video and once you click on that you might see a page that looks
00:01:46.159 something like this with uh basically three dots in the top right it's going to look different cuz it's a different
00:01:51.439 file but hit the three dots in the top right and then just hit edit copy and that will enable you to be able to start
00:01:58.320 working in your own copy of the file so this is the real file that we'll be working in today what you're going to
00:02:00.000 No text
00:02:04.799 need is an interactive broker account because we want to do this with paper trading and this is the brokerage firm
00:02:11.120 that has the most notoriously well-known paper trading platform and what paper
00:02:16.560 trading is is it's a way to basically have a fake portfolio where you simulate
00:02:22.160 trades so you're not risking your own real money you're implementing some sort of uh strategy or trying out some
00:02:28.560 trading strategy and seeing how it does without real money on the line so the first step here is going to be to click
00:02:35.920 this link and you can find this either here or in the description to sign up for an interactive broker account so I
00:02:42.800 just held control and then leftclicked on it and then this pops up so what you're going to want to do is click open
00:02:48.640 an account and then start application so once you do that you can just go through the basic steps it's like opening any
00:02:55.120 type of brokerage account you don't actually have to put any money in but you just need the account so that you can use the paper trading functionality
00:03:02.159 so it may take depending on like when you actually do it one to two business days to get approved just as a side note
00:03:09.920 and then once you have the account or even before then you can start at least setting some stuff up so we need their
00:03:10.000 No text
00:03:16.879 software called Trader Workstation or TWWS and we need the API for that as
00:03:22.400 well so then you can hold control and leftclick on this and then we're going
00:03:28.640 to have this page right here pop up and this is all about the API for this software the main things you're going to
00:03:35.280 need to do are to scroll down and see where it says download trader workstation now you can click that and
00:03:42.319 then you'll see something pop up basically in your downloads after you download the latest one so let's say I
00:03:47.680 wanted to do uh TWWS latest and hit download now that's going to pop up in
00:03:54.000 my downloads on my computer and then you can just run this installer and just click you know next next next next apply
00:04:01.680 essentially and then what we can also do is go back to that same page that we
00:04:08.080 were on before and a little bit below where we downloaded the trader
00:04:13.120 workstation we need to keep scrolling to download the uh API software so we get
00:04:20.560 down to this section where it says download the TWWS API and you'll just do the same thing where you hit this and
00:04:26.800 then you'll hit uh I agree and then depending on you know what type of uh
00:04:31.919 system you have I would just download the stable one for either uh Mac or Unix
00:04:36.960 or Windows whichever you have so if you have Windows you click there and then you'll go through the same thing where you just click on that installer it
00:04:43.040 should be in your downloads on your computer and hit you know next next apply essentially now once you've got
00:04:48.000 No text
00:04:50.080 Trader Workstation installed and the Trader Workstation API installed and
00:04:55.440 you've been approved for the account that you signed up for in this step we're going to configure the uh Trader
00:05:02.680 Workstation for the API access and you can do that by following the steps that I've written out right here so first
00:05:10.240 let's open up Trader Workstation so I'm going to click here and type tws and we see Trader Workstation pop up i'll click
00:05:16.960 on that now here you're going to see that you can either do live trading or paper trading so you want to make sure
00:05:23.680 to click on the paper trading and it should look red like this and then you'll just type in your username and
00:05:30.160 your password when you log in you should see something uh similar to this so we'll
00:05:37.440 just go ahead and click okay and now we're just going to do a few steps to make sure that the API is looking uh
00:05:44.880 correct so let's go ahead and put these side by side just so we can see both
00:05:50.880 steps while we're uh working on this thing so we need to go up to edit and
00:05:57.840 then global configuration and then once we get to global configuration there's
00:06:02.960 something right here called API so we'll click on that and then we'll go to uh
00:06:08.000 settings so now there's a few things we want to make sure that we have either
00:06:13.600 checked or unchecked so the first one is going to be this enable activex socket
00:06:20.400 client we want to make sure that this is checked and then we want to make sure that we have unchecked read only API and
00:06:28.160 then also we want to make sure that we have unchecked allow connections from localhost only which you can see right
00:06:35.680 down here and then also we want to verify that this uh socket port right
00:06:40.880 here is 7497 which is uh what we'll use for paper trading so once you've got all
00:06:47.840 that set that should be pretty good there's another thing we might want to do is that we might want to add some
00:06:54.639 trusted IPs so we're going to go to down here where it says trusted IPs and click
00:07:01.599 create uh click create and then you can just grab from here uh this one here
00:07:08.160 copy it with control C paste it in there and hit okay i already put it in there so I don't really need to put it in
00:07:14.479 there twice and then the other one that you'll do is uh this one right here as
00:07:19.680 well with the same process so you have both those trusted IPs that'll make it so that we don't have to like approve
00:07:25.199 every time we connect it will just trust this system to connect to here so now
00:07:30.960 once we've done that you can go ahead after you made these changes hit apply
00:07:36.160 um and then you're going to have to restart Trader Workstation so you'll just close out and relog in the same way
00:07:42.000 No text
00:07:42.479 now in order to get our uh data lore cloud notebook right this isn't on our
00:07:47.680 local computer it's running in the cloud in order to get it to connect to
00:07:53.280 Interactive Brokers we need to basically create some sort of tunnel on our own
00:07:58.479 computer where we can connect the two and so how we're going to do that is that if you're on Windows you'll go into
00:08:05.360 the search and look for command prompt if you're on Mac you'll look for terminal so I'm on Windows i'm going to type command prompt and I'm going to
00:08:13.120 pull that up and then I'm going to grab this right here hit Ctrl C and I'm going
00:08:20.240 to put it to right here and hit enter so now that we see this green right here forwarding TCP connections from and
00:08:27.039 basically we've created something that this system can access to connect to
00:08:32.320 Trader Workstation here now let's go ahead on our next step and import some of the Python libraries that we're going
00:08:33.000 No text
00:08:39.120 to need to connect we can see the two libraries that we need to import listed right here so we need to import this one
00:08:46.080 nest asyncio I guess is how you would pronounce that now let's hit control C
00:08:51.120 on that and then I'm going to go right here to environment and then I will paste it in there and hit enter now
00:08:58.800 we're going to see this option here i'm going to just click on this little download icon so now we're installing
00:09:06.000 that one and then let's go and grab this one as well ib in sync all right let's
00:09:12.720 put it in there as well enter and then let's download that one
00:09:19.040 as well now that we've installed both it wants us to restart the kernel so let's go ahead and click restart kernel which
00:09:25.920 means it's just going to restart uh this whole notebook now that these packages are installed so we should have
00:09:31.920 everything that we need from this point forward we're going to allow data's in-built AI assistant to write a bunch
00:09:32.000 No text
00:09:39.680 of code for us so what we're going to do is be using these prompts that I've
00:09:46.160 listed here to have it write the code so now that everything's set up we need to connect this software here to the trader
00:09:54.240 workstation software so what we can do is just take this prompt that I've already written here to uh we'll copy
00:10:02.000 that with C and then this little icon is ask AI so we'll paste it in there and
00:10:08.000 then we'll hit run there we go it wrote some code for us
00:10:14.640 let's accept and run that and see how it does okay so it looked like uh it had a
00:10:21.680 few errors and then finally it successfully connected to Trader Workstation so if you did this step
00:10:27.120 where you added these trusted IPs to Trader Workstation you won't really see anything pop up over here if you didn't
00:10:33.040 do that step you'll see a box pop up that you have to say uh I approve of this connection happening so now let's
00:10:40.000 No text
00:10:41.519 do another step where we want to basically see if it's working and we're going to do that by trying to get the
00:10:48.959 server in uh trader or in their reactive brokers to tell us what time it is so
00:10:54.000 it's just a basic test to make sure that we've connected properly now let's run
00:10:59.200 this prompt to have it write the code for us now let's accept and run that okay it's
00:11:06.640 successful and it's giving us that uh UTC time so we can see that we've got it
00:11:12.720 properly configured already now the next prompt is going to have us just test a
00:11:14.000 No text
00:11:18.560 buy order for one share of the S&P 500 index spy so right now if you look in my
00:11:25.200 account because I've been playing around and doing a lot of different stuff with it I currently have a portfolio with
00:11:30.800 just uh 92 shares of SPY and there's nothing else actually in this portfolio so if we have it correctly write this
00:11:38.000 code and execute it then we should be up to 93 shares of SPY so let's take this
00:11:44.079 prompt here hit C then go to the AI assistant and run that
00:11:52.000 so it wrote a lot of code a bit more than I expected we can see that basically it's trying to buy one uh spy
00:11:59.120 with a smart order method in USD and it wants to buy uh one single share and so
00:12:05.920 then we're going to have some basically error catching our prints to see how it does let's accept and
00:12:11.480 run so we get an error that says that this IB object has no attribute uh
00:12:17.200 market order so then let's hit fix with AI and give it a chance to basically
00:12:23.360 just correct itself so it wrote some new code where
00:12:29.279 basically it's now importing that market order from that library and rerunning
00:12:35.279 okay we see that it ran and now I can see right here it popped up bought uh one spy so if I go back to here now we
00:12:44.079 should have gone from the uh 92 shares to the 93 shares and yep we're now at 93
00:12:50.720 shares now let's say let's test if we can just sell that one share that we
00:12:51.000 No text
00:12:56.160 just bought so that we can go back down to 92 shares so this is where we're going to have the AI write code to
00:13:03.120 basically sell one of these shares so the prompt is now uh let's close our position by selling the share we just
00:13:09.920 bought and so we're going to ask it basically to write that code and uh do some verification so I'll copy that then
00:13:17.279 I'll hit this ask AI put the prompt in there and then I'll run
00:13:23.240 that now we'll hit accept and run and now we can see it worked because it
00:13:29.279 popped up down here we sold one share of SPY and we can also see that it printed
00:13:34.639 it here so if we come back we can see that we went down from 93 back to
00:13:41.079 92 now this next step we want to potentially retrieve historical stock
00:13:42.000 No text
00:13:46.959 prices from Interactive Brokers so we're basically just going to be asking for
00:13:53.680 300 days of daily price history for SPY from Interactive Brokers so this is just
00:13:59.920 free data maybe we can build some strategy around that data maybe in the
00:14:05.680 future so this free data is never going to be as useful but it's a start if you
00:14:11.760 don't want to pay any money so let's grab that prompt go to ask AI put the
00:14:18.000 prompt in there and then hit this run here now it wrote some code for us to
00:14:25.120 grab basically 300 days of uh spy shares now let's hit accept and run and see how
00:14:32.480 that performs okay perfect we can see that it just printed the head there which means it
00:14:37.839 prints just five rows so we've got 300 days of shares um it for me it's April
00:14:43.440 2nd right now so 300 trading days would be about 3 months more than a year so
00:14:48.639 that's why it goes back to this point in time now we want to do something with this data let's say that we want to uh
00:14:51.000 No text
00:14:56.560 create some simple strategy and I'll just read the prompt so next we're going
00:15:01.920 to say now that we have our historical spy data let's implement a simple moving average crossover strategy please create
00:15:09.040 code that calculates 20-day and 50-day moving averages identifies buy and sell signals at crossover points and
00:15:15.839 visualizes the results with price history moving averages and signal markers on a chart so let's grab this uh
00:15:23.040 here and once we see the chart I'll kind of explain more what I'm like meaning by this prompt so let's run this one
00:15:34.000 so we can see it actually wrote quite a bit of code so basically what it's going to do is take a 20-day moving average of
00:15:40.639 the SPY prices and then also a 50-day moving average of the SPY prices and
00:15:46.320 then it's going to say "Hey when the 20-day becomes larger than the 50-day
00:15:52.160 that's a buy signal." Basically we're saying that if the average of the price in the last 20 days crosses over to be
00:15:58.959 higher than the average of the price in the last 50 days that means that the momentum is going is that this stock is
00:16:04.880 basically pushing upward the value is pushing upward let's buy it at that time
00:16:10.480 however if the 20-day moving average becomes less than the 50-day moving average that means that the momentum has
00:16:17.920 then cooled off the stock price is falling and we want to basically catch the momentum of it decreasing by selling
00:16:24.959 at that time let's see if this code actually works so let's accept and run
00:16:30.160 boom that actually looks pretty good so basically we can see that this uh 20-day
00:16:36.000 moving average line is the green line and then the 50-day moving average line is the red line so at this point we can
00:16:42.240 see that the 20-day fell below the 50-day and then it's saying that would have been a time to have sold and then
00:16:49.759 now we can see there's like this uptick in momentum where this 20-day right here
00:16:54.959 crosses above the 50-day moving average and then it's saying to buy at this time so we would have bought at basically
00:17:00.639 this price this green triangle which is like I don't know 530 bucks or something and then we would wait to have sold
00:17:07.280 until after the 20-day moves below the 50-day so that's actually at this point
00:17:12.799 so you would have captured I don't know a small amount of profit at that point but then it's telling you hey the 20-day
00:17:19.119 crossed back above the 50-day here buy here then eventually you wait till it crosses below again sell there so that
00:17:25.280 would have been a netted a large profit anyways I'm not really saying that this
00:17:30.480 strategy I did any back testing about it working we're just doing something you know simple to see if we can get get
00:17:36.320 this bot to connect properly and start doing some trades so this is looking good uh so far so now what we want to do
00:17:44.000 No text
00:17:44.000 is actually implement the strategy so right now all we did was make a graph based on past historical data but what
00:17:51.440 we want to do now is basically go ahead and try to implement a strategy so that
00:17:56.480 it works into the future and so I've created a prompt that's a little too
00:18:01.520 long to read but if you want to pause and read it feel free to go ahead basically we're just asking it to build this uh trading system and so then let's
00:18:09.679 go ahead and ask the AI and hit
00:18:14.760 run there we go it wrote a uh quite a bit of code for us and so now it's basically putting in these rules um into
00:18:22.320 practice with actual buys and sells that connect to we can see this IB connect
00:18:27.520 here is connecting to our trader work system so that it would actually make trades based on this so let's accept and
00:18:33.840 run and see how it goes so monitoring system is running uh use the stop event
00:18:40.799 set command to stop it safely the system has stopped so basically it started and then it stopped so then this next one is
00:18:46.000 No text
00:18:48.320 where we're want going to want to create code to basically run this system uh
00:18:55.120 when we want to run it right so that we have more control over when it starts and stops so we're saying now let's
00:19:01.600 create a simple demonstration of our trading system in action write a code cell that starts our monitoring system
00:19:07.840 displays information messages to the user about what's happening and optionally includes a way to
00:19:13.039 automatically stop after a certain time period for demonstration purposes this gives users a clear example of how to
00:19:19.280 activate and control the automated trading system in a real world scenario so basically it's probably going to write something where it's like it'll
00:19:24.960 just automatically we'll start it and then it'll stop after a set amount of time and we've kind of left it up to the AI to determine how long it's actually
00:19:32.080 going to run this for okay so it seems to have decided that it's just going to run this system
00:19:38.400 for 600 seconds or 10 minutes so let's accept and run that and then we should
00:19:43.600 see something where basically it's starting the system to run for 10 minutes it seems to still be running
00:19:50.720 even though this message said that it stopped so let me uh just clarify something about this so we've used free
00:19:57.520 data and generally free data is just going to be this information where we can see the dayend prices like this this
00:20:03.200 is not going to be useful for a highfrequency algorithmic trading system
00:20:08.720 because that would only give you the ability to basically make trades at the open of the day or the close like it's
00:20:17.200 basically giving you one piece of information every day when you try to build some sort of like algo trading bot
00:20:24.080 you probably want live data that's happening almost every second for it to be more useful so you can take advantage
00:20:30.640 of price movement so this is not super useful to build one that's based on this
00:20:35.919 but we would if if we wanted to actually use this one that we just did you'd basically need to make sure that it's
00:20:41.280 running when the new data comes in each night or yeah basically whenever the
00:20:46.799 close data comes in and then it has the opportunity to make one trade based on that that's not really what I envisioned
00:20:52.960 when I went out to try to create an algorithmic trading bot what I really wanted to do was create one where I have
00:20:55.000 No text
00:20:59.520 data like every second happening and then it's going to be making like trades
00:21:04.640 in real time you know but that costs money so this tutorial is going to
00:21:10.640 continue and we're going to use the live data but it's just with basically the
00:21:16.159 disclaimer that probably you're just going to watch from now on to see what I'm doing because essentially this live
00:21:23.200 data I'm going to stop this by the way at this point this live data is actually really not cheap so I have a basically a
00:21:31.280 subscription for uh this service here that's like $200 a month and I the reason I'm using that is because it's
00:21:38.240 has a realtime data so I'm going to be able to pull in data every you know
00:21:43.520 second and start having the bot make decisions and I can get unlimited data so that's where we're going from here so
00:21:49.000 No text
00:21:50.640 once we start using the real time data that's going to require a lot more computing power up until this point we
00:21:57.840 have been running if I had run here and then change machine uh I've been using this CPU L it has four CPU cores and 16
00:22:06.480 GB RAM it's really weak but in order to basically use a more powerful algorithm
00:22:14.000 I'm going to need to use more powerful hardware and so what I'm probably going to do is bump it up to this like CPU XXL
00:22:20.960 which gives me 48 CPU cores and 96 GB of RAM so we can run basically a more
00:22:27.200 powerful realtime algorithmic strategy however what you need for that is basically the account that allows you to
00:22:34.799 do that so when we were over on this page and you signed up for like the cloud free you would be able to use
00:22:35.000 No text
00:22:40.720 these for uh more time but only for 1 month and then it would need to switch
00:22:45.840 over to this cloud plan where essentially then it starts to become more pricey so this company I've been
00:22:53.039 partnering with them for nearly or maybe even more than a year now so they've actually hooked up uh my viewers with
00:23:00.400 this analyze like Ryan promo code that uh just gives like 50% off for this uh
00:23:06.799 cloud plan I think even either yearly or monthly billing so then if you want to
00:23:12.000 No text
00:23:12.000 use that then what we'll do at this point in the tutorial is we're going to switch this from this weaker machine to
00:23:19.919 this more powerful machine so that we can start uh running more powerful strategies now when we do that it's
00:23:27.200 going to reset this whole application and kernel so I'm going to need to go back up to the top and I'm going to have
00:23:34.400 to basically get reconnected so I'm going to need to connect here again one thing I found when I disconnect and
00:23:40.960 reconnect it helps to just stop this instance here and restart it so I'm going to hit Ctrl C twice to basically
00:23:48.159 close that then I'm going to hover over this and Ctrl + C and then Ctrl +V to
00:23:53.200 paste this and then we're going to open up that connection one more time and now let's rerun this so we should connect
00:24:00.480 again so we can see that we've successfully connected and then let's just test our connection to get server
00:24:06.000 time boom perfect now let's do one more test where we just test a buy order there we go we see that we bought down
00:24:12.880 here in this bottom corner and then we're going to test a sell order so let's run that boom perfect we see that
00:24:18.640 we just sold one so now we know we're all hooked up and connected at this
00:24:23.679 point um I'm going to stop having the AI write the code and just use code that I've written because it's a little bit
00:24:29.840 complicated i have included some prompts beyond this point that people could use to have the AI write the code for them
00:24:37.039 or you can just use the code that I've already written that would probably be easier because it did take a long time for me to get all this stuff working so
00:24:43.000 No text
00:24:44.159 basically with this you know service here you need an API key i have my own API key that I'm putting in here it's
00:24:50.720 going to be blurred out on your screen and then once we have the API key that's how we get connected to the service so
00:24:57.840 I'm going to run that and I'm going to have it print my API key out just to confirm that we set it up correctly and
00:25:04.159 then the next thing we're going to basically start importing some packages and that we actually need to connect uh
00:25:12.640 to Polygon right so we need to connect so we can get their live data and that's where some of these things are going to
00:25:19.120 be coming into play so let's run that and we can see that we have imported all of the libraries successfully now we're
00:25:26.880 going to set up basically what we're going to use as a data structure to take
00:25:32.240 our uh data in from the polygon API and so we'll run this and it should print
00:25:38.640 that we have set it up uh successfully that's perfect and now here we're going
00:25:42.000 No text
00:25:43.840 to generate some logic so think about what we were doing earlier we were
00:25:49.120 basically running this strategy that was going to be every uh 20 days and 50 days
00:25:55.600 and then we're trying to sell on momentum of these days or buy on the momentum of these days so what we're
00:26:00.640 going to do with this strategy with Polygon is actually instead of doing it in days we're going to do it every 20
00:26:07.039 and 50 seconds so we're going to try to capture these super shortterm movements in the stock price over 20 and 50
00:26:14.000 seconds and basically run the same strat so if the 20- second moving average crosses above the 50-second moving
00:26:20.480 average that's an upward momentum signal and we're going to buy whereas if the 20-cond moving average falls below the
00:26:25.760 50-cond moving average that is a sell signal because the momentum is decreasing again I have not back uh back
00:26:32.400 tested these strategies i have no idea if they would actually work this for me is just a proof of concept of whether I
00:26:39.679 can actually configure a bot that will do realtime trading in a paper trading account so let's now uh create basically
00:26:47.840 this logic of what I just described in code everything I just said we're trying to put it into code right now and
00:26:54.320 perfect this shows us that we set everything up properly now here we're going to write a websocket callback
00:26:56.000 No text
00:27:00.799 function for polygon io on message on air on close on open that will process
00:27:06.159 incoming trade data authenticate our API key and subscribe to spy ticker data so
00:27:12.240 this is really where we're trying to connect everything to Polygon and I
00:27:17.520 added a little note that while you could try this prompt it's unlikely that the AI is just going to oneshot all this
00:27:23.840 code because it's kind of a lot of code and it is a bit complicated so now let's run that and now we can see that we have
00:27:31.039 this little message at the bottom polygon websocket thread started and then on my actual Polygon account I can
00:27:37.279 go into the back end and go here to usage websocket you can see that we now have one active uh websocket connection
00:27:45.600 that's been happening for about a minute and it has not disconnected so we are connected that is great now that we've
00:27:52.000 No text
00:27:53.440 connected let's create basically a visualization function so the prompt
00:27:58.799 that you could use for this is create a function to visual visualize our real-time trading data including price
00:28:04.399 chart moving averages and buy and sell signals the function should update periodically as new data arrives so what
00:28:12.640 we're doing is we're taking those 20 second 50cond moving averages and we're going to just live them so that we can
00:28:19.039 see how is it basically going to in real time generate these buy and sell signals
00:28:24.559 so this is just going to create a function it's not actually going to run it yet we're just creating this little
00:28:30.080 algorithm that's going to display how our trading strategy is looking so let's go ahead and let's run that and then
00:28:35.000 No text
00:28:37.120 right here we're going to have to actually create a function that's going to make this whole system start when we
00:28:45.279 actually do want it to start including connect to polygon so you can use this
00:28:51.039 prompt to basically generate this type of code it's fairly straightforward and then let's run this function so we just
00:28:57.440 ran that now this is going to be the most complicated thing of the whole algorithm i can't even it it took me a
00:28:58.000 No text
00:29:03.840 really long time to get all this to work so I did give a prompt that you know you could use to get something to generate
00:29:09.039 something like this but what I would say is that it is super unlikely that AI
00:29:14.960 would oneshot this code and what I mean by oneshot is write it all this way in
00:29:20.240 one single try there's just too much code here and it's a little bit too complicated so it took me quite a while
00:29:27.440 working with the AI through basically an iterative process where I have it write code it tries to write code it fails we
00:29:35.360 talk about why it failed then have it try to go again and just over and over and over until I got something that
00:29:41.039 actually works so essentially what we're going to be doing here is we're going to
00:29:46.159 want to execute trades so we're saying execute trades false so we don't want it
00:29:51.600 to actual actually execute trades in real time yet we will get to that that
00:29:57.279 that's when we'll change this to true but for now it's false and then this is position size so this would be the
00:30:02.880 number of shares that we're going to trade so we're just going to trade one share of spy at a time uh we could up
00:30:09.679 this to 10 shares or 20 shares or whatever but just as an example let's stick to one and then we're also going
00:30:17.039 to say the max number of positions allowed right now we could say it's five we don't want it to trade more than five
00:30:22.640 whatever maybe I'll up it to 10 it's not going to make any more than 10 trades on this algorithm and then we have a cool
00:30:28.000 down period of 10 seconds between trades so basically if we make one trade and
00:30:34.720 then it has another buy or sell signal it's not allowed to trade until after 10
00:30:40.000 seconds so then once we've done all that now there's going to be some complicated
00:30:45.919 functions where one is we're basically connecting to you know uh interactive
00:30:51.240 brokers another is going to be used to update our current position another is going to use to be uh exocate whether we
00:30:58.159 should make a trade based on the signal of that you know the 20 second moving average crossing above or below the
00:31:03.760 50-second moving average and then the most complicated function of all is this
00:31:09.039 uh start trade trading listener which is basically going to be a separate thread
00:31:15.520 used to monitor for trading signals and it has all the logic in there of whether we want to basically make buys or sell
00:31:23.600 orders and this this one's quite complicated so if you want to like try something like this you might want to
00:31:30.399 just copy my code rather than trying to write it yourself so let's run this and
00:31:35.000 No text
00:31:35.679 now here's where we're actually going to start a visualization of this whole strategy that we've created this isn't
00:31:41.600 going to actually execute any trades it's just going to show uh the system working in real time with live uh every
00:31:49.519 second data so let's go ahead and run that so now it's creating a graph and what's going to happen is it's going to
00:31:56.000 get a little bit more data and the graph will start to make a bit more sense and it'll refresh in a second here okay
00:32:03.200 there we go so we're basically going to see and there's some uh I would say some
00:32:09.279 issues with like the data in terms of some like spikes and falls so we're
00:32:15.440 seeing when the the the spikes are with this price so I think one thing you could do to basically make the algorithm
00:32:22.080 more accurate would be to um have something that detects when these little
00:32:27.360 this like spikes come in that likely is inaccurate uh spy pricing but aside from
00:32:34.080 that so we're seeing this like 20 second moving average is the green line and
00:32:39.279 then the uh 50second moving average is the red line and then it's doing the same thing when we see a cross over
00:32:46.000 green crosses above red that's a buy signal when uh red crosses above green
00:32:51.200 that's a sell signal and then so it's just going to operate like that so now
00:32:56.000 No text
00:32:57.200 we can do something where we're going to actually set it up so that we enable it
00:33:02.240 to execute live trades so we're tra we're switching from false to true for
00:33:07.840 executing the trades and you could use this prompt to write some code like this so let's run that and
00:33:15.240 now one thing that you should do which I've already done is that you can go and
00:33:22.080 to run and then where it has this background computation it has it's usually set to uh different I forget
00:33:30.159 what the default is but I changed it to never turn off so if I want to basically just keep running the system so it
00:33:35.600 doesn't just automatically turn off i'm making that logic so there and now this
00:33:40.000 No text
00:33:41.440 is where we're actually going to start the system so this is we're telling it to write a Python code that starts a
00:33:48.480 background thread to run start trading listener function continuously ensure it
00:33:53.519 doesn't block the main thread also print a message showing whether autotrading is enabled based on the value of a global
00:34:01.440 variable execute trades so this code is going to start running it so what I want
00:34:06.720 to do now is actually put this up side by side so we can see our trader
00:34:12.000 workstation actually running here and so let's let's just run this thing and now
00:34:18.320 we can see we started running it and we just sold one share of spy so it went from 92 down to 91 now it's going to
00:34:25.918 have that cool down period of 10 seconds where it can't make any trades until it
00:34:31.520 gets another signal about whether it should actually buy or sell so we see it just got another sell signal so we just
00:34:38.639 sold one so we went from 91 all the way down to 90 so our system is properly
00:34:44.800 working it took quite a while for me to get this working okay then we just sold another so this price must be falling
00:34:51.359 right now this makes me happy you know I stand like a proud dad watching his only
00:34:56.399 son that made it and we'll see if this could actually generate profits one
00:35:01.680 thing I'm thinking is that this likely will not generate profits uh one thing I might go ahead and just stop this system
00:35:08.480 for a sec we can just talk about what actually happened so I'll do run uh and then we can just stop machine so that'll
00:35:14.000 No text
00:35:15.680 just stop everything and now we can go look at our trade history and we can see that it was making these we did three
00:35:22.960 trades on this where we they basically traded one traded 17 seconds after the
00:35:28.480 other one and the other one waited the 10-second cool down period then had a signal after 11 seconds so one thing I'd
00:35:35.040 like to clarify is that basically this commission is like $12 uh per cell and so with this type of
00:35:43.520 strategy it would not be feasible on small volume so this would be basically guaranteed to lose money well why is
00:35:50.240 that because we're trading something that's only worth
00:35:55.560 $559.74 and then we're like doing these quick buys and sells and every time we do it we lose a dollar which is
00:36:01.839 basically going to be like an immediate loss of like2% so this is something where you
00:36:08.320 would have to really increase the order size so you'd have to do it in much
00:36:14.400 larger volumes if the commission is $1 so you'd have to basically back test and make sure that based on this logic that
00:36:21.760 the trades that you're making are generally netting you a profit that's larger than that commission with this
00:36:27.839 system that I just built where we're only trading one single stock and the commission is that high for that one
00:36:33.599 share you're super unlikely to be able to generate a profit that way this was
00:36:38.000 No text
00:36:39.280 really just a proof of concept for something like this i wanted to be able to see if I could write rules have a bot
00:36:45.599 that connects to a cloud uh machine that's powerful enough to operate a
00:36:51.040 realtime trading strategy and then get it to generate trades based on that the
00:36:56.240 next step that I want to look at is basically seeing if there's things that I can implement in a paper trading
00:37:02.320 account trying different rules and see if they could possibly net a profit and
00:37:08.240 so one thing I might even think about doing in the future is that this software has these like super powerful
00:37:14.160 machines with these like Nvidia tensor core machines that are used for super
00:37:19.440 advanced AI machine learning models and I want to get some data and see if I can
00:37:25.359 actually use a eye models to try to gen come up with some strategy that might be
00:37:31.760 able to net some profit and then based on these strategies try to run it in the paper trading account and see what
00:37:38.160 actually happens and if I actually find something that really does work then take some of my actual real money put it
00:37:44.000 into a real brokerage account and then run that strategy to try to generate
00:37:49.359 real profit there's a few steps between now and then but I have some goals in mind for this and maybe I can update
00:37:55.599 with a video in the future if I actually you know find some time to play around with this and see what's possible thank
00:38:02.480 you for watching this video and if you'd like to see a video where I use this same tool to use code to back test a
00:38:11.200 trading strategy feel free to click right here
