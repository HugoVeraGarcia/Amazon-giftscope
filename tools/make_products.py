#!/usr/bin/env python3
"""Builds data/products.json from finalists.csv + the latest price check + the editorial notes below.

Run:  python3 tools/make_products.py
Prices/ratings come from data/verified_<date>.txt (asin,price,rating,reviews), checked on Amazon.com.
Links are built as https://www.amazon.com/dp/<ASIN>?tag=giftscope-20
"""
import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TAG = "giftscope-20"
CHECKED = "2026-10-02"

# Removed after the 2 Oct price check
SKIP = {
    "B0DMWBSJMP",  # Monster High doll jumped to $79.76 (third-party price)
    "B0GLT23RV6",  # Elf on the Shelf dress set: only 5 ratings
}

# theme slugs: superheroes dinosaurs building stem arts dolls pretend-play tech vehicles outdoor music games plush learning
# ASIN: (display name, theme, top pick?, blurb)
ED = {
    # Superheroes
    "B09CWP2G71": ("Heroes of Goo Jit Zu Marvel Mini 6-Pack", "superheroes", False,
                   "Six squishy, stretchy mini Marvel heroes filled with goo. Great for collectors and a fun stocking upgrade."),
    "B0BS4GVV4D": ("Marvel Avengers Ultimate Protectors 8-Figure Pack", "superheroes", True,
                   "Eight 6-inch Avengers in one box, so the whole team is ready for battle on day one."),
    "B0DVBDD7YP": ("Iron Man and His Awesome Friends Role Play Set", "superheroes", False,
                   "Wearable hero gear for preschool fans of the Disney Junior show, built for pretend missions around the house."),
    "B073VBBX59": ("Marvel Spider-Man Kids Digital Watch", "superheroes", False,
                   "An easy-to-read digital watch with a Spider-Man design: a small, useful gift for kids learning to tell time."),
    "B07ZHS1L15": ("Marvel Super Hero Adventures 5-Inch Figure 5-Pack", "superheroes", False,
                   "Five chunky, kid-sized heroes made for little hands. A strong pick for 3- to 5-year-olds."),
    "B0CCSR4V9P": ("Marvel Hulk Gamma Smash Fists", "superheroes", True,
                   "Giant green Hulk fists with smash sounds. Big, loud fun that kids remember from the moment they open the box."),
    "B0BQRWJ877": ("Marvel Spider-Man Youth Deluxe Costume", "superheroes", False,
                   "A padded deluxe Spider-Man suit for dress-up all year, not just on Halloween."),
    "B0FMS8XPT8": ("LEGO Marvel Spider-Man vs. Ghost Rider Motorcycle", "superheroes", False,
                   "A quick, affordable LEGO build with two heroes and a bike. An ideal stocking stuffer for Marvel fans."),
    "B0G5QL2HBQ": ("LEGO Marvel Advent Calendar 2026", "superheroes", False,
                   "A small Marvel LEGO build behind every door, so the countdown to Christmas becomes a daily treat."),
    # Dinosaurs
    "B0D5GLT4R4": ("JOYIN 17-Piece Dinosaur Figures with Play Mat", "dinosaurs", False,
                   "A starter herd of realistic dinosaurs plus a play mat to build their world. Great value for preschoolers."),
    "B0B9HV6SVG": ("JOYIN 13-in-1 Dinosaur Carrier Truck", "dinosaurs", True,
                   "A transport truck that carries a dozen mini dinosaurs, combining two big passions in one toy."),
    "B08FMB1TGS": ("Gzsbaby 6-Piece Jumbo Soft Dinosaurs", "dinosaurs", False,
                   "Big, soft and safe dinosaurs for toddlers who love to squeeze, stomp and roar."),
    "B07S6FDHPN": ("Create A Dinosaur World Road Race Track", "dinosaurs", False,
                   "A flexible race track through a dinosaur world. Kids build the route, then race cars past the T. rex."),
    "B09P4TS8KX": ("VERTOY Remote Control Walking Velociraptor", "dinosaurs", False,
                   "A remote-control raptor that walks and roars. The 'wow' gift for dino-obsessed kids ages 5 and up."),
    "B0D3D61QS9": ("Dinosaur Magnetic Tiles with Movable Dinos", "dinosaurs", False,
                   "Magnetic building tiles plus dinosaurs, so kids build habitats and play out stories."),
    "B09CTX4BW5": ("Take-Apart Dinosaur Toys with Electric Drill", "dinosaurs", False,
                   "Kids use a toy drill to take dinosaurs apart and rebuild them. Hands-on fun that builds fine motor skills."),
    "B00K89KFX0": ("VTech Chomp and Count Dino", "dinosaurs", False,
                   "A push-along dino that teaches counting, colors and songs. A favorite first dinosaur for toddlers."),
    # STEM & science
    "B00008BFZH": ("Snap Circuits Jr. SC-100 Electronics Kit", "stem", True,
                   "Over 100 real electronics projects with snap-together parts. A classic STEM gift that kids actually use."),
    "B07XTKJXPT": ("Smartivity Robotic Mechanical Hand", "stem", False,
                   "Build a working robotic hand from wood parts and learn how hydraulics and levers work."),
    "B00IUAAK2A": ("ThinkFun Gravity Maze", "stem", True,
                   "A marble-run logic game with 60 challenges, from easy to expert. Screen-free brain training."),
    "B08P5XGHJG": ("Smartivity DIY Pinball Machine", "stem", False,
                   "Kids build their own working pinball machine, then play it. Engineering with a payoff."),
    "1338603450": ("Klutz LEGO Gear Bots", "stem", False,
                   "Build moving LEGO creatures with gears and a motor. A great bridge from LEGO to real mechanics."),
    "B00VKRK7K0": ("Snap Circuits Arcade SCA-200", "stem", False,
                   "The next step up from Snap Circuits Jr.: kids build programmable games and electronic gadgets."),
    "B08V16FFFC": ("Thames & Kosmos Roller Coaster Engineering", "stem", False,
                   "Design and test roller coasters while learning the physics of speed, gravity and loops."),
    "B000FGECAI": ("Educational Insights Kanoodle", "stem", False,
                   "A pocket-size 3D puzzle game with hundreds of challenges. Perfect for car rides and stockings."),
    "B092W7D64G": ("Rubik's Cube Original 3x3", "stem", False,
                   "The original puzzle cube. A cheap gift that can keep a curious kid busy for weeks."),
    "B079D7XHSY": ("Moose Games Flipslide Handheld Puzzle", "stem", False,
                   "A fast handheld color-matching game with four modes. A screen-free stocking stuffer."),
    "B093CPZYR8": ("National Geographic Amazing Chemistry Set", "science", True,
                   "Dozens of safe chemistry experiments, from crystals to fizzy reactions, with clear instructions."),
    "B0876F6STP": ("National Geographic Science Magic Kit", "science", False,
                   "Magic tricks powered by science: kids learn the experiment, then perform the trick for the family."),
    "B082ZLM39R": ("National Geographic Earth Science Kit", "science", False,
                   "Real geodes to crack, plus crystals, fossils and a volcano experiment in one big kit."),
    "B09XGMHGJ3": ("Doctor Jupiter My First Science Experiments Kit", "science", False,
                   "Simple, safe experiments designed for preschool and early-grade scientists."),
    "B0C5MMYRJ3": ("UNGLINGA 150 Experiments Science Kit", "science", False,
                   "150 experiments in one box. Lots of variety for a curious kid who wants to try everything."),
    "B0FFSSWTB6": ("1000X Handheld Digital Microscope for Kids", "science", False,
                   "A handheld digital microscope with a screen, so kids can explore bugs, leaves and coins up close."),
    "B00B1Z6EPS": ("GeoSafari Kidnoculars", "science", False,
                   "Real binoculars sized for small faces, with easy focus, for backyard and nature walks."),
    # Building
    "B00NHQF6MG": ("LEGO Classic Large Creative Brick Box", "building", True,
                   "790 bricks in 33 colors with idea booklets. The one LEGO set every family uses for years."),
    "B0CGY4J7QT": ("LEGO Creator 3-in-1 Flatbed Truck with Helicopter", "building", False,
                   "Three builds in one box: a truck, a plane and a hovercraft. More play for the price."),
    "B0BLJ4FDT4": ("LEGO Creator 3-in-1 Space Shuttle", "building", False,
                   "A small 3-in-1 space set under $10, ideal as a stocking stuffer or party gift."),
    "B0G5QKD8ZS": ("LEGO Star Wars Advent Calendar 2026", "building", True,
                   "24 days of Star Wars mini builds and minifigures. A countdown that kids and adults love."),
    "B0G5QJP2BW": ("LEGO City Advent Calendar 2026", "building", False,
                   "A daily LEGO City surprise through December, with a holiday play mat."),
    "B0FMS84RFJ": ("LEGO Speed Champions Back to the Future Time Machine", "building", False,
                   "The DeLorean in LEGO form, a detailed build for older kids and nostalgic parents."),
    "B0FMS854MN": ("LEGO Sonic the Hedgehog Speedster Lightning", "building", False,
                   "A small Sonic set with a quick build, priced for stockings and party bags."),
    "B0DJ19R8H7": ("LEGO Minecraft The Nether Lava Battle", "building", False,
                   "A mini Minecraft scene under $10. An easy win for young Minecraft fans."),
    "B0FMS7CRHX": ("LEGO Botanicals Daisies", "building", False,
                   "Buildable flowers that never wilt. A relaxing build for teens, moms and grandmas."),
    "B00AU56C5W": ("PicassoTiles 100-Piece Magnetic Tiles", "building", True,
                   "100 magnetic tiles for castles, towers and rockets. Open-ended play that lasts from age 3 to 8."),
    "B0GGTK4YCT": ("MAGNA-TILES microMAGS Travel Set", "building", False,
                   "Mini magnetic tiles in a travel case for restaurants, flights and road trips."),
    "B007GE75HY": ("MEGA BLOKS First Builders Big Building Bag", "building", False,
                   "Big, easy-grip blocks in a storage bag. The classic first building toy."),
    "B000068CKY": ("Melissa & Doug 100 Wooden Building Blocks", "building", False,
                   "Solid wood blocks in four colors and nine shapes. A timeless toy that survives siblings."),
    "B0BXQ6NRRN": ("LEGO Harry Potter Hogwarts Castle and Grounds", "building", True,
                   "A detailed micro-scale Hogwarts with the castle, grounds and boathouse. A display piece for Potter fans."),
    "B0DRW6KZKF": ("LEGO Technic Ferrari FXX K", "building", False,
                   "A Technic supercar with working steering and a moving engine. A great first Technic set."),
    # Arts & crafts
    "B07M6CDS77": ("COO&KOO Charm Bracelet Making Kit", "arts", False,
                   "Charms, beads and chains to design custom bracelets. Great for crafty kids and sleepovers."),
    "B0C23NBZ6W": ("Nollh DIY Journal Kit for Girls", "arts", True,
                   "A journal plus stickers, washi tape and supplies to decorate it. Encourages writing and creativity."),
    "B0DTB2N2D9": ("Crayola Marker Airbrush Spray Art Kit", "arts", False,
                   "Turns markers into an airbrush for spray-paint art without the mess of paint."),
    "B0F9WFBTP5": ("Skillmatics Aqua Puffs Unicorns", "arts", False,
                   "Puffy water-activated paint that dries into 3D unicorn art. Easy cleanup for parents."),
    "B00JM5GZGW": ("Play-Doh 36-Pack Case of Colors", "arts", False,
                   "36 cans of Play-Doh in a carry case, enough for months of creations."),
    "B07GKWLBN2": ("Water Doodle Mat", "arts", False,
                   "Draw with water, watch it disappear, start again. Mess-free art for toddlers."),
    "B0BGN2HQHH": ("Kikidex Magnetic Drawing Board", "arts", False,
                   "A colorful magnetic doodle board with stamps. No ink, no mess, endless drawings."),
    # Dolls
    "B0GCC4HQRP": ("KPop Demon Hunters Rumi Golden Singing Doll", "dolls", True,
                   "A singing Rumi doll from the hit movie. One of the most requested dolls this season."),
    "B0GCCHQ77Z": ("KPop Demon Hunters Zoey Fashion Doll", "dolls", False,
                   "Zoey in her stage outfit, ready to join Rumi for KPop Demon Hunters fans."),
    "B0CB6JWL75": ("Barbie Gymnastics Doll & Playset", "dolls", False,
                   "Barbie with a balance beam and accessories. Active play for young gymnastics fans."),
    "B0FDGZDRGS": ("Barbie Skipper Babysitters Inc. Playset", "dolls", False,
                   "Skipper babysits with baby dolls and accessories. Big on storytelling for a small price."),
    "B0978H7YYB": ("Disney Store Rapunzel Classic Doll", "dolls", False,
                   "The Disney Store's classic Rapunzel, with her signature long hair and dress."),
    "B08TTTW6TY": ("Gabby's Dollhouse Gabby Girl Doll", "dolls", False,
                   "An 8-inch Gabby doll for preschool fans of the show, under $15."),
    "B0F18MNB6C": ("Imagimake Magnetic Dress-Up Princess", "dolls", False,
                   "Magnetic outfits to mix and match on wooden princess figures. Screen-free play on the go."),
    "B0F5TWR4ZR": ("Aori Lifelike 17-Inch Baby Doll", "dolls", False,
                   "A soft, realistic baby doll with accessories for kids who love to play parent."),
    # Pretend play
    "B01B1V10KA": ("Melissa & Doug Scoop & Serve Ice Cream Counter", "pretend-play", True,
                   "A wooden ice cream shop with scoops, cones and toppings. Pretend play kids return to for years."),
    "B09PD6YWF1": ("Meland Doctor Kit with Puppy", "pretend-play", False,
                   "A doctor kit with a puppy patient and carry case. Great for calming fears about checkups."),
    "B01COSEDKS": ("VTech Drill and Learn Toolbox", "pretend-play", False,
                   "A toolbox with a working toy drill that teaches numbers and shapes while kids 'fix' things."),
    "B095LT69HN": ("Hollyhi 58-Piece Kids Washable Makeup Kit", "pretend-play", False,
                   "Washable, kid-safe makeup in a case. Dress-up fun that comes off with soap and water."),
    "B01N037GIU": ("Monobeach Princess Castle Play Tent with Lights", "pretend-play", False,
                   "A castle tent with star lights, a cozy hideout for reading, napping and pretend play."),
    "B08H8DT32C": ("Tiny Land Wooden Play Kitchen", "pretend-play", True,
                   "A modern wooden play kitchen with realistic details. The big gift that becomes the center of the playroom."),
    # Tech & gadgets
    "B0D38GBHCS": ("Amazon Fire HD 8 Kids Pro Tablet (6-12)", "tech", True,
                   "A kids' tablet with parental controls, a slim case and a 2-year worry-free guarantee for older kids."),
    "B0CVDTKNVZ": ("Amazon Fire HD 8 Kids Tablet (3-7)", "tech", False,
                   "A tablet in a kid-proof case with a year of Amazon Kids+ and parental controls."),
    "B093TL7BMB": ("Toniebox Audio Player Starter Set", "tech", True,
                   "A screen-free audio player: kids place a figure on top and stories or songs start to play."),
    "B0D541M5C6": ("Yoto Mini Kids Audio Player", "tech", False,
                   "A pocket audio player with card-based stories and music. Screen-free and travel-friendly."),
    "B0D2JGYX3F": ("Nex Playground Active Play System", "tech", False,
                   "A motion-based game console that gets kids moving instead of sitting. Big hit for families."),
    "B0C42948MY": ("Tamagotchi Original Starry Shower", "tech", False,
                   "The original virtual pet, back for a new generation, at a stocking-friendly price."),
    "B0B68W6ZMT": ("Goopow Kids Digital Camera", "tech", False,
                   "A sturdy, kid-sized digital camera for photos and video. A first camera for little creators."),
    "B0BTM72KLT": ("ESOXOFFORE Kids Instant Print Camera", "tech", False,
                   "Takes a photo and prints it instantly on paper kids can color. No ink needed."),
    "B0FXX575KP": ("Video Walkie Talkies for Kids (2-Pack)", "tech", False,
                   "Walkie talkies with video screens. Perfect for siblings and backyard adventures."),
    "B0CHS2VNHC": ("YLL Kids Karaoke Machine with 2 Mics", "music", False,
                   "A small karaoke speaker with two mics, so kids can sing duets at home."),
    "B071FJ1763": ("Riwbox Light-Up Kids Bluetooth Headphones", "tech", False,
                   "Wireless headphones with LED lights and a volume limit designed for kids."),
    "B0CXJDDJ9X": ("DJI Mini 4K Drone", "tech", True,
                   "An easy-to-fly 4K camera drone under 249 g. A premium gift for teens who like photo and video."),
    "B0BWNYPCT1": ("Fujifilm Instax Mini 12 Instant Camera", "tech", True,
                   "Point, shoot and print credit-card-size photos. The most popular instant camera for teens and tweens."),
    "B09FXFSY6R": ("Tatybo RGB Gaming Headset", "tech", False,
                   "A budget gaming headset with RGB lights and a mic for PS5, Xbox, Switch and PC."),
    "B0H93MFZ34": ("Mini Projector with WiFi 6 and Bluetooth", "tech", False,
                   "A compact projector with built-in apps for movie nights on a bedroom wall."),
    "B0DY918NGN": ("Sony WH-CH520 Wireless Headphones", "tech", False,
                   "Lightweight Sony headphones with long battery life. A reliable everyday pick for teens."),
    "B097NDLV1L": ("Retro Bluetooth Speaker", "tech", False,
                   "A cute retro-style speaker that doubles as room decor. An easy teen gift under $15."),
    "B0BXP35GZQ": ("DAYBETTER Smart LED Strip Lights 200 ft", "tech", False,
                   "App-controlled LED strips that sync to music. The most-asked-for teen room upgrade."),
    "B0F2GYMC8H": ("Meta Quest 3S 128GB VR Headset", "tech", False,
                   "Mixed-reality headset with games, fitness and apps. A big wow gift for teens (13+)."),
    "B0F3GWXLTS": ("Nintendo Switch 2", "tech", True,
                   "Nintendo's new console with a bigger screen and more power. The top wish-list item of 2026."),
    "B0793JTRKG": ("LEGO Architecture Statue of Liberty", "building", False,
                   "A 1,600-piece display model of Lady Liberty for teens and adults who love a long build."),
    # Vehicles & RC
    "B0CTWHSSM8": ("QUNREDA 4WD Stunt RC Car", "vehicles", False,
                   "A double-sided stunt car that flips and spins 360 degrees. Built for bumps and crashes."),
    "B0CT8KCNBD": ("Gesture-Sensing RC Stunt Car", "vehicles", False,
                   "Drive with a remote or steer with hand movements via a watch controller. Pure wow factor."),
    "B0GYWVLG6M": ("RC Wall-Climbing Gecko", "vehicles", False,
                   "A remote-control gecko that climbs walls and windows. A surprising gift kids show off."),
    "B073PVRSDL": ("HAIBOXING 1:18 All-Terrain RC Car", "vehicles", False,
                   "A fast hobby-grade RC truck for grass, dirt and gravel, for older kids ready for speed."),
    "B0DR3PT4JM": ("Hot Wheels Monster Trucks Oversized Bigfoot", "vehicles", False,
                   "An oversized Bigfoot monster truck that kids can crash and bash. Under $15."),
    "B0G1TZTY5K": ("Hot Wheels 2026 Advent Calendar", "vehicles", False,
                   "24 days of Hot Wheels cars and accessories, with a play mat to race them on."),
    "B08K3N4RR9": ("Tonka Steel Classics 4x4 Pickup Truck", "vehicles", False,
                   "A real steel Tonka truck built to last through sandboxes and siblings."),
    "B08J4FJ63D": ("Disney Pixar Cars Radiator Springs 3-Pack", "vehicles", False,
                   "Lightning McQueen and friends in die-cast, at a small price for big Cars fans."),
    "B0BYYV9185": ("iPlay iLearn Rocket Space Toy", "vehicles", False,
                   "A rocket that holds astronauts and a rover, with lights and sounds for preschool space fans."),
    "B0BTBV51KY": ("iPlay iLearn Press-to-Go Toddler Cars", "vehicles", False,
                   "Press-and-go cars that zoom without batteries. Simple, sturdy toddler fun."),
    "B0CBJFSP3G": ("12V Mercedes-AMG GT Kids Ride-On Car", "vehicles", True,
                   "A licensed 12V ride-on with a parent remote. The big Christmas morning gift for ages 3 to 5."),
    # Outdoor
    "B0CCYMV1T1": ("Gotrax KS1 Kids 3-Wheel Kick Scooter", "outdoor", False,
                   "A light-up 3-wheel scooter with lean-to-steer, made for first-time riders."),
    "B01EN6LTAQ": ("Razor A Kick Scooter", "outdoor", True,
                   "The classic folding Razor scooter, light and tough. A gift kids ride for years."),
    "B0DDQ4FQHK": ("SEREED Toddler Balance Bike", "outdoor", False,
                   "A light balance bike that teaches steering and balance, the easiest path to a pedal bike."),
    "B01C967BQS": ("Little Tikes Cozy Coupe", "outdoor", False,
                   "The iconic foot-to-floor car toddlers drive around the yard and the living room."),
    "B00G466HBU": ("Stomp Rocket Jr. with 8 Rockets", "outdoor", False,
                   "Stomp on the pad and send foam rockets flying. No batteries, endless backyard fun."),
    "B07PM8J9GJ": ("National Geographic LED Air Rocket Launcher", "outdoor", False,
                   "Light-up rockets that fly up to 100 feet. Works in the evening too."),
    "B0D5JX1QQF": ("Hover Soccer Light-Up Ball", "outdoor", False,
                   "A hovering soccer disc with LED lights for indoor play without broken lamps."),
    "B08P29SC84": ("Nerf Vortex Aero Howler Football", "outdoor", False,
                   "A whistling foam football that flies far and is easy to catch."),
    "B08MV8HMD3": ("Nerf Elite Disruptor Blaster", "outdoor", False,
                   "A quick-draw Nerf blaster with a 6-dart drum. A Nerf battle starter under $15."),
    "B07FNQFLJ5": ("Toss and Catch Ball Yard Game", "outdoor", False,
                   "Paddle-and-ball catch game for backyards, beaches and family gatherings."),
    "B0D56JMVH9": ("Toddler Basketball Hoop", "outdoor", False,
                   "An adjustable hoop with balls, sized for toddlers and preschoolers."),
    "B0CLGB5BCJ": ("VEVOR Kids Trampoline with Enclosure", "outdoor", False,
                   "An indoor/outdoor kids trampoline with a safety net and handle to burn off energy."),
    "B0CJJ9ZBSK": ("FanttikRide C9 Pro Kids Electric Scooter", "outdoor", False,
                   "An electric scooter with speed limits for kids 6-12. A big gift for kids who outgrew kick scooters."),
    # Early learning (baby & toddler)
    "B07B6ZN7P8": ("LeapFrog Learning Friends 100 Words Book", "learning", True,
                   "Touch a picture and hear the word in English and Spanish. A bestselling first-words toy."),
    "B06XNQDR8J": ("LeapFrog 2-in-1 LeapTop Touch", "learning", False,
                   "A toddler 'laptop' that teaches letters, numbers and music. Little ones love copying parents."),
    "B071LQQHPZ": ("VTech Busy Learners Activity Cube", "learning", False,
                   "Five sides of buttons, shapes and songs. A small cube that keeps toddlers busy."),
    "B0CPN4YBQ6": ("Fisher-Price Little People Caring for Animals Farm", "learning", False,
                   "A farm playset with animals and sounds for imaginative play from age 1."),
    "B0CPHTTKBZ": ("Gojmzo Montessori Busy Board", "learning", False,
                   "Latches, zippers and buckles on one board to build fine motor skills."),
    "B0CX24138S": ("Ms. Rachel Speak & Sing Doll", "learning", True,
                   "Ms. Rachel sings songs and says phrases. A huge hit with toddlers who watch her show."),
    "B0CBQRXNVW": ("Fisher-Price Glow and Grow Kick & Play Piano Gym", "learning", False,
                   "A play gym with a kick piano and lights, from tummy time to sitting up."),
    "B01J94K9OY": ("Skip Hop Baby Activity Center", "learning", True,
                   "A 3-stage activity center that grows from seat to table. Lots of play for babies."),
    "B01EUNA0WK": ("Baby Einstein Neptune's Ocean Discovery Jumper", "learning", False,
                   "A jumper with a rotating seat, ocean toys, lights and music for active babies."),
    "B075R8BXXC": ("Lovevery The Play Gym", "learning", True,
                   "A premium 5-stage play gym designed with child development experts. A favorite registry gift."),
    "B07MPCCDM7": ("Baby Einstein 4-in-1 Kickin' Tunes Play Gym", "learning", False,
                   "A music-and-language play gym with a kick piano, from newborn to toddler."),
    "B07CRSXMW8": ("VTech Sit-to-Stand Learning Walker", "learning", True,
                   "An activity panel for sitting babies that becomes a push walker for first steps."),
    "B07NXDJ52C": ("Sassy Stacks of Circles Stacking Rings", "learning", False,
                   "Textured stacking rings for grasping, teething and stacking. Under $10."),
    "B0CD42KQ3K": ("Montessori Sensory Teething Toy", "learning", False,
                   "A silicone sensory toy with pull strings and textures for teething babies."),
    # Music
    "B007XVYSDE": ("VTech KidiBeats Kids Drum Set", "music", False,
                   "A small electronic drum set with songs and learning modes for toddlers."),
    "B0GN8PRZMT": ("VTech Kidi Star DJ Mixer Pro", "music", False,
                   "A kid DJ mixer with effects and beats to make their own tracks."),
    "B0DMF8JZYS": ("LeapFrog Strum and Count Wooden Guitar", "music", False,
                   "A wooden toy guitar that teaches counting and colors while kids strum."),
    "B0D1VJMSQG": ("Portable Karaoke Machine with 2 Wireless Mics", "music", False,
                   "A Bluetooth karaoke speaker with two wireless mics for family sing-alongs."),
    # Family games
    "B0DWGVM7RY": ("Flip 7 Card Game", "games", True,
                   "A quick push-your-luck card game that's easy to learn. A family game night winner under $10."),
    "B077Z1R28P": ("Taco Cat Goat Cheese Pizza", "games", False,
                   "A fast, silly slap card game for kids and adults. Lots of laughs in 10 minutes."),
    "B06XZ9K244": ("SKYJO Card Game", "games", False,
                   "A simple strategy card game the whole family can play. Highly rated and addictive."),
    "B08VFGZRR6": ("Five Crowns Card Game", "games", False,
                   "A five-suit rummy game with rotating wilds, a classic for family gatherings."),
    "B00000DMF5": ("Candy Land", "games", False,
                   "The classic first board game. No reading needed, perfect for preschoolers."),
    # Plush
    "B0F2GPDFZZ": ("FurReal Sally the Silly Hippo", "plush", False,
                   "An interactive plush hippo with silly sounds and reactions."),
    "B0CFBCJL3K": ("Emotional Support Dumplings Plush", "plush", False,
                   "A cute dumpling plush with a sweet message. A viral favorite for tweens, teens and adults."),
    "B0DK7X9WGJ": ("Squishmallows Star Wars Grogu 8-inch", "plush", False,
                   "Grogu in super-soft Squishmallow form, for Squishmallow and Star Wars fans alike."),
    "B0CZ4K7TW8": ("Disney Store Lightning McQueen Plush", "plush", False,
                   "A soft Lightning McQueen to cuddle at bedtime, from the Disney Store."),
}

THEME_FIX = {"science": "stem"}


def ages(s: str):
    a, b = (int(x) for x in s.split("-"))
    return a, b


def main():
    rows = {r["asin"]: r for r in csv.DictReader(open(DATA / "finalists.csv"))}
    ver = {}
    vfile = sorted(DATA.glob("verified_*.txt"))[-1]
    for tok in vfile.read_text().split():
        a, p, r, n = tok.split(",")
        ver[a] = (p, r, n)
    out = []
    for asin, row in rows.items():
        if asin in SKIP:
            continue
        if asin not in ED:
            raise SystemExit(f"missing editorial for {asin} {row['name']}")
        name, theme, top, blurb = ED[asin]
        p, r, n = ver.get(asin, ("", "", ""))
        price = float(p or row["price"])
        a0, a1 = ages(row["ages"])
        out.append({
            "asin": asin,
            "name": name,
            "theme": THEME_FIX.get(theme, theme),
            "age_min": a0,
            "age_max": a1,
            "price": round(price, 2),
            "rating": float(r or row["rating"]),
            "reviews": int(n or 0),
            "image": row["image"],
            "top": top,
            "blurb": blurb,
            "url": f"https://www.amazon.com/dp/{asin}?tag={TAG}",
        })
    extra = set(ED) - set(rows) - SKIP
    if extra:
        raise SystemExit(f"editorial without product: {extra}")
    json.dump({"checked": CHECKED, "tag": TAG, "products": out},
              open(DATA / "products.json", "w"), indent=1, ensure_ascii=False)
    print(len(out), "products ->", DATA / "products.json")


if __name__ == "__main__":
    main()
