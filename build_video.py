#!/usr/bin/env python3
"""Render the eight-act narrated edit from the supplied ZIPs and voiceover."""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ZIPS = ["Image .zip", "Image1.zip", "Image2.zip", "Image3.zip", "Image4.zip", "Image5.zip", "Image6.zip", "ImageI.zip", "MIUI.zip"]
VOICE = ROOT / "imagine_waking_up_tomorrow_and_the_sun_looks_wro.mp3"
OUT = ROOT / "The_Year_Without_a_Summer.mp4"
MANIFEST = ROOT / "edit_manifest.json"
ASSET_DIR = Path("/tmp/tambora_video_assets")
WORK_DIR = Path("/tmp/tambora_video_render")
W, H, FPS, FADE = 1280, 720, 24, 6
FRAMES = {1: 2730, 2: 4374, 3: 2106, 4: 4326, 5: 3157, 6: 2843, 7: 3120, 8: 1884}
ACTS = {
 1: ("THE YEAR WITHOUT A SUMMER", "Imagine the sun going dim"),
 2: ("MOUNT TAMBORA ERUPTS", "Sumbawa, Indonesia - 1815"),
 3: ("THE INVISIBLE PARASOL", "How ash and aerosols dimmed the sun"),
 4: ("A SUMMER THAT NEVER CAME", "Crops fail. Winter comes early."),
 5: ("MIGRATION AND FRANKENSTEIN", "A climate shock changes human history"),
 6: ("A WORLD IN WEATHER CHAOS", "Strange skies across continents"),
 7: ("COULD IT HAPPEN AGAIN?", "What science can tell us today"),
 8: ("THE HUMAN COST AND LEGACY", "A global lesson in resilience"),
}

# Explicitly place important/ambiguous scenes; all remaining assets use the
# prompt-derived subject names and a manually reviewed act vocabulary.
RULES = {
 1: ["character_opening_door_with_coffee", "stick_figure_in_dark_bedroom", "stick_figure_waking_up_in", "stick_figure_looking_out_window", "stick_figures_looking_out_window", "cartoon_sun_at_noon", "stick_figure_floating_sun", "yellow_sun_waving", "smoke_blocking_sun", "stick_figure_under_murky_sun", "hand_dragging_sun", "stick_figure_viewing_slider_bar", "character_viewing_june_wall", "calendar_page_rips", "calendar_pages_flipping", "stick_figure_breath_freezing", "stick_figure_exhaling_freezing", "stick_figure_pointing_at_calendar", "stick_figure_viewing_stone_numbers", "stick_figure_watches_spinning_clock", "stick_figure_watching_time_change", "stick_figure_viewing_hourglass", "stick_figure_near_town_sign", "stick_figure_near_tavern_signboard", "stick_figure_holding_history_book", "stick_figure_unlocking_file_folder", "stick_figure_examining_question", "stick_figure_pointing_upward", "stick_figure_reaching_toward", "stick_figure_dropping_ink_curtain", "character_pushing_clapperboard", "stamp_on_movie_clapperboard", "character_standing_before_pinned", "stick_figure_inside_house"],
 2: ["arrow_pointing_to_sumbawa", "character_looking_at_map", "map_zooms_to_sumatra", "stick_figure_viewing_indonesia_map", "stick_figure_viewing_map_animation", "stick_figure_viewing_global_dist", "stick_figure_hovering_flag_over", "stick_figure_reading_distance_sign", "stick_figure_holding_pointer_stick", "character_hovering_over_comparis", "stick_figure_cracks_cartoon_meter", "stick_figure_viewing_gauge_chart", "character_viewing_magma", "stick_figure_holding_volcano_trophy", "stick_figure_tending_rice_terraces", "stick_figure_in_indonesian_village", "stick_villagers_trading_fruit", "stick_figure_catching_fish", "stick_sailor_rowing_boat", "stick_soldiers_aiming_muskets", "british_soldiers_jumping", "stick_figure_holding_tea", "stick_figure_sailing_tall_ship", "stick_figure_holding_wooden_chec", "stick_figure_blasting_soundwaves", "stick_figure_viewing_lava_flow", "stick_figure_viewing_volcanic_cr", "stick_figure_viewing_pyroclastic", "stick_figure_watching_tsunami_wave", "tsunami_crashing_over_coastal_boats", "tsunami_ripples_washing_indonesi", "ash_burying_bamboo_huts", "stick_figure_watching_ash_fall", "stick_figure_beside_flickering_l", "stick_figure_on_scorched_wasteland", "volcano_pulling_train_switch", "stick_figure_near_mount_tambora", "stick_figure_near_cartoon_crater", "stick_figure_near_glowing_volcano", "stick_figure_near_mountain", "stick_figure_looking_up_peak", "stick_figure_measuring_distance", "stick_figure_measuring_mountain", "stick_figure_reveals_date_text", "stick_figure_unrolling_scroll_text", "stick_figure_viewing_ticking_dyn", "stick_figure_on_exploding_island", "stick_figure_dodging_falling_rocks", "stick_figure_character_causing", "stick_figure_observing_volcano", "stick_figure_shakes_mountain", "stick_figure_above_magma_cavern", "stick_figure_and_small_volcano", "stick_figure_in_tropical_landscape", "stick_figure_holding_glowing_lan", "stick_figure_standing_on_grass", "stick_figure_watching_approachin", "stick_figure_watching_smoke_plume", "stick_figures_looking_at_smoke", "volcanic_clouds_erupting_from_mo", "volcano_awakens_with_angry_eyes", "mount_tambora_erupting", "mount_tambora_swelling_and_snapping", "mountain_peak_blasts_off_pieces", "cartoon_cloud_roaring_down_mountain", "forest_turning_into_glowing_embers", "smoke_pouring_from_mountain", "ash_column_shooting_past_clouds", "black_cloud_engulfs_cartoon_frame", "diagram_of_mount_tambora_eruption", "bluebirds_perched_on_crater"],
 3: ["pillar_punches_through_earth", "stick_figure_drops_ice_cube", "stick_figure_tapping_earth_bubble", "stick_figure_holding_umbrella_in", "sunbeams_bounce_off_earth_bubble", "temperature_gauge_needle_moves_left", "stick_figure_releasing_toxic_gas", "stick_figure_character_in_atmosp", "stick_figure_illustrating_scienc", "stick_figure_showing_atmospheric", "stick_figure_in_stratosphere", "stick_figure_scatters_light_beams", "stick_figure_under_falling_anvil", "stick_figure_inspecting_glowing", "stick_figure_examining_acid_droplet", "stick_figure_fusing_chemicals", "stick_figure_atmospheric_pressur", "droplets_marching_around_cartoon", "sulfuric_acid_aerosol_appears", "sun_arrows_bouncing_off_parasol", "sunbeam_arrow_hits_droplet", "sunbeam_arrows_ricochet_in_space", "yellow_arrows_flying_toward_parasol", "yellow_ball_bumping_blue_droplet", "black_and_yellow_cloud_spreading", "thermometer_bulb_shatters_into_ice", "thermometer_mercury_slides_down", "thermometer_showing_negative_tem", "character_pointing_at_giant_ther", "stick_figure_opens_giant_parasol", "stick_figure_drops_black_anvil"],
 4: ["stick_figure_viewing_normal_temp", "stick_figure_viewing_temperature", "stick_figure_farmer_planting_seeds", "stick_figure_planting_corn_seeds", "stick_figure_planting_markers", "stick_figure_farmer_giving_thumb", "stick_figure_comparing_harvest", "stick_figure_viewing_corn_sprouts", "stick_figure_farmer_holding_soil", "stick_figure_farmer_farming_dirt", "stick_figure_farmer_imagining_ha", "stick_figure_thinking_about_farm", "stick_figure_farmer_in_snow", "stick_figure_farmer_looking_up", "stick_figure_farmer_looks_up", "stick_figure_farmer_panicking", "stick_figure_farmer_scratching_head", "stick_figure_farmer_sweating_on", "stick_figure_frozen_in_ice", "stick_figure_holding_ice_cube", "stick_figure_holding_umbrella", "stick_figure_in_muddy_rain", "stick_figure_kneeling_in_snow", "stick_figure_looking_at_house", "stick_figure_reading_emergency", "stick_figure_has_no_idea", "stick_figure_reading_snowy_sign", "stick_figure_rubbing_arms", "stick_figure_shattering_summer", "stick_figure_watching_rain", "stick_figure_wearing_winter_scarf", "stick_figures_shivering_in_winte", "character_examining_frosty_tree", "character_viewing_northeastern", "character_writing_in_diary", "globe_transition_to_europe_map", "grim_reaper_swinging_scythe", "stick_farmer_in_heavy_rain", "stick_farmer_staring_at_wheat", "stick_farmer_writing_in_diary", "stick_farmers_pulling_wooden_plows", "stick_figure_brushing_snow", "stick_figure_drops_wooden_hoe", "stick_figure_facing_arctic_arrow", "stick_figure_falling_leaves_anim", "stick_figure_farmer_dropping_to", "stick_figure_near_dead_stalks", "stick_figure_planting_corn_seeds", "stick_figure_on_farm_field", "stick_figure_observing_flooded", "stick_figure_facing_arctic_arrow", "stick_figure_viewing_european_ic", "stick_figure_watching_withered_corn", "stick_farmer", "farmer_enduring_snowy_wind_storm", "farmer_in_snow_holding_watering", "farmer_stares_at_ruined_crops", "farmer_walking_in_frost-bitten", "ice_block_squashes_stick_figure", "ice_crystals_freezing_camera_lens", "ice_spikes_spreading_on_fence", "lone_farmhouse_in_new_hampshire", "price_shooting_upward", "river_overflowing_village_bridges", "rooster_weathervane", "snow_covering_berkshire", "snowflakes_falling_over_cartoon_map", "stagecoach_stuck_in_snowbank", "stick_figure_drops_wooden_hoe", "stick_figure_in_muddy_rain", "two_stick_figures_walking_past"],
 5: ["stick_figure_in_frontier_town", "stick_figure_packing_covered_wagon", "stick_figure_farmer_in_wagon", "stick_figure_hammering_wooden_sign", "stick_figure_pointing_compass_west", "stick_figure_building_map", "stick_figure_burying_signpost", "stick_figure_character_reading_n", "stick_figure_character_standing_b234", "stick_figure_holding_feather_quill", "stick_figure_woman_holding_book", "stick_figure_woman_tossing_in", "stick_figure_woman_writing_in", "stick_figure_watching_candle_flame", "stick_figure_at_villa_diodati", "stick_figure_in_gothic_laboratory", "stick_figure_lounging_in_armchair", "stick_figure_pacing_before_padlock", "stick_figure_poet_reading_poetry", "stick_figure_closing_book", "stick_figure_merges_cartoon_fire", "stick_figure_monster_rising_in", "monster_stick_figure_hand_twitches", "stick_figure_handing_out_paper", "stick_figures_near_fireplace", "stick_figures_sitting_on_sofa", "woman_writing_manuscript_by_cand", "artist_painting_volcanic_sunset", "frankenstein_book_in_erupting_vo", "cartoon_storybook_revealing_stor", "nightmare_thought_cloud_expandin", "book_slams_on_wooden_table", "map_zooms_over_lake_geneva", "map_highlights_indiana_and_illinois", "red_migration_arrow_entering_ohio", "us_map_expanding_westward", "covered_wagons_leaving_snowy_town", "stick_pioneers_on_crowded_trail", "stick_figures_loading_covered_wa", "stick_figure_viewing_population", "newspaper_headline_spinning_onto", "character_standing_by_lakeside"],
 6: ["red_arrow_shoots_from_indonesia", "stick_figure_watching_crimson_su", "character_revealing_chaotic_weat", "character_visiting_italian_village", "figure_viewing_church_steeple", "red_spotlight_over_new_england", "stick_doctor_pointing_at_fog", "stick_figure_character_amidst_haze", "stick_figure_character_standing_", "stick_figure_experiencing_extrem", "stick_figure_holding_postcard", "stick_figure_in_red_snow", "stick_figure_looking_at_cloud", "stick_figure_over_surreal_horizon", "stick_figure_overlooking_cartoon", "stick_figure_reacting_to_sky", "stick_figure_ringing_bell", "stick_figure_screaming_at_laundry", "stick_figure_tangles_wind_arrows", "stick_figure_under_night_sky", "stick_figure_under_toxic_sky", "stick_figure_viewing_bizarre_ter", "stick_figure_viewing_floating_icons", "stick_figure_viewing_red_lining", "stick_figure_viewing_shattered", "stick_figure_viewing_weather_icons", "stick_figure_watching_lightning", "stick_figures_in_town_square", "stick_figures_looking_at_sky", "stick_figures_pointing_at_sky", "stick_figures_praying_during_lig", "stick_figures_staring_at_sky", "stick_figures_walking_through_fog", "stick_official_hammering_red_pro", "wind_blows_against_dry_fog", "stick_figure_on_london_street", "stick_figure_observing_weather_i"],
 7: ["stick_figure_character_near_earth", "stick_figure_encasing_earth", "stick_figure_facing_city_skyline", "stick_figure_facing_warning_tria", "stick_figure_flips_globe", "stick_figure_rejecting_science_icon", "stick_figure_spinning_globe", "stick_figure_spinning_globe_anim", "stick_figure_using_telescope", "stick_figure_viewing_split_graphic", "stick_figure_wearing_gas_mask", "stick_meteorologist_examining_te", "stick_scientist_pulling_electric", "stick_figure_gentlemen_examining", "stick_figure_transforming_coin"],
 8: ["icons_appearing_over_earth", "stick_figure_connecting_glowing", "stick_figure_crying", "stick_figure_hat_on_ground", "stick_figure_holding_earth", "stick_figure_near_wooden_bowl", "stick_figure_tracking_world_map", "stick_figure_viewing_historical", "sprout_and_quill_pen_growing", "stone_statue_melting_snow_rain", "farmer_stares_at_ruined_crops", "stick_figure_farmer_dropping_to", "stick_figure_near_dead_stalks", "stick_figure_watching_withered_corn", "lone_farmhouse_in_new_hampshire"],
}

# Most important frames lead each act; supporting frames are sorted by filename.
ORDER = {
 1: ["character_opening_door", "waking_up", "dark_bedroom", "looking_out_window", "sun_at_noon", "floating_sun", "sun_waving", "smoke_blocking", "murky_sun", "dragging_sun", "slider_bar", "june_wall", "calendar_page", "calendar_pages", "breath_freezing", "exhaling_freezing", "pointing_at_calendar", "stone_numbers", "spinning_clock", "time_change", "hourglass", "town_sign", "tavern_sign", "history_book", "unlocking_file", "examining_question", "pointing_upward", "reaching_toward", "ink_curtain", "clapperboard"],
 2: ["arrow_pointing_to_sumbawa", "viewing_indonesia_map", "map_zooms_to_sumatra", "looking_at_map", "hovering_flag", "near_mount_tambora", "near_cartoon_crater", "near_glowing_volcano", "near_mountain", "tropical_landscape", "measuring_distance", "reading_distance", "measuring_mountain", "sleeping_with_nightcap", "swelling_and_snapping", "shakes_mountain", "reveals_date", "magma_red_text", "mountain_peak_blasts", "mount_tambora_erupting", "ash_column", "smoke_pouring", "volcanic_clouds", "cloud_roaring", "escaping_erupting", "dodging_falling", "pyroclastic", "forest_turning", "exploding_island", "watching_tsunami", "tsunami_crashing", "tsunami_ripples", "ash_burying", "watching_ash_fall", "scorched", "tending_rice", "indonesian_village", "villagers_trading", "catching_fish", "sailor_rowing", "soldiers", "pulling_train_switch"],
 3: ["pillar_punches", "illustrating_scienc", "atmospheric", "stratosphere", "toxic_gas", "fusing_chemicals", "acid_droplet", "sulfuric_acid", "droplets", "yellow_ball", "sunbeam", "parasol", "earth_bubble", "scatters_light", "thermometer", "temperature_gauge", "drops_ice_cube"],
 4: ["planting", "giving_thumb", "imagining_ha", "comparing_harvest", "thinking_about_farm", "corn_sprouts", "holding_soil", "farming_dirt", "normal_temp", "viewing_temperature", "frosty_tree", "arctic_arrow", "winter_scarf", "snow", "ice_block", "ice_crystals", "ice_spikes", "frozen_in_ice", "kneeling_in_snow", "brushing_snow", "wind_storm", "heavy_rain", "muddy_rain", "watching_rain", "river_overflow", "flooded", "wheat", "withered", "dead_stalk", "price", "emergency", "stagecoach", "diary"],
 5: ["map_highlights_indiana", "population", "red_migration_arrow", "westward", "covered_wagon", "wagon", "pioneers", "frontier_town", "compass_west", "hammering_sign", "burying_signpost", "lake_geneva", "lakeside", "villa_diodati", "standing_b234", "feather_quill", "woman_writing", "woman_holding", "woman_tossing", "manuscript", "candle_flame", "poet_reading", "sitting_on_sofa", "near_fireplace", "armchair", "nightmare", "gothic", "monster_rising", "hand_twitches", "frankenstein_book", "storybook", "book_slams", "closing_book", "newspaper_headline"],
 6: ["red_arrow_shoots", "chaotic_weather", "red_spotlight", "amidst_haze", "dry_fog", "fog", "red_snow", "weather_icons", "observing_weather", "bizarre", "crimson", "looking_at_cloud", "reacting_to_sky", "over_surreal", "overlooking_cartoon", "walking_through_fog", "lightning", "praying", "town_square", "ringing_bell", "screaming_at_laundry", "postcard", "red_lining", "shattered", "toxic_sky", "night_sky"],
 7: ["viewing_split_graphic", "facing_city", "warning", "rejecting_science", "meteorologist", "scientist", "telescope", "spinning_globe", "flips_globe", "encasing_earth", "character_near_earth", "gas_mask", "gentlemen", "transforming_coin"],
 8: ["wooden_bowl", "crying", "ruined_crops", "farmer_dropping", "dead_stalks", "withered_corn", "exhausted", "lone_farmhouse", "hat_on_ground", "historical", "tracking_world_map", "connecting_glowing", "holding_earth", "icons_appearing", "statue_melting", "sprout_and_quill"],
}

REPRISES = {
 1: ["Character_opening_door_with_coffee", "Stick_figure_waking_up_in", "Stick_figure_looking_out_window", "Cartoon_sun_at_noon", "Hand_dragging_sun_icon", "Smoke_blocking_sun_in", "Calendar_page_rips_to_June", "Stick_figure_breath_freezing", "Stick_figure_viewing_slider_bar"],
 2: [],
 3: ["Stick_figure_fusing_chemicals", "Sulfuric_acid_aerosol_appears", "Stick_figure_opens_giant_parasol", "Temperature_gauge_needle_moves_left"],
 4: ["Ice_block_squashes_stick_figure", "Snowflakes_falling_over_cartoon_map", "Stick_farmer_in_heavy_rain", "River_overflowing_village_bridges", "Stick_farmer_staring_at_wheat", "Price_shooting_upward", "Character_writing_in_diary", "Stick_figure_shattering_summer"],
 5: ["Covered_wagons_leaving_snowy_town", "US_map_expanding_westward", "Red_migration_arrow_entering_Ohio", "Map_zooms_over_Lake_Geneva", "Artist_painting_volcanic_sunset", "Stick_figure_woman_writing_in", "Nightmare_thought_cloud_expandin", "Frankenstein_book_in_erupting"],
 6: ["Red_arrow_shoots_from_Indonesia", "Stick_figure_in_red_snow", "Wind_blows_against_dry_fog", "Stick_figure_watching_crimson_su", "Stick_figure_viewing_weather_icons", "Stick_figure_watching_lightning", "Stick_figures_walking_through_fog", "Character_revealing_chaotic_weat", "Stick_figure_holding_postcard"],
 7: ["Stick_figure_facing_city_skyline", "Stick_figure_facing_warning_tria", "Stick_figure_viewing_split_graphic", "Stick_meteorologist_examining_te", "Stick_scientist_pulling_electric", "Stick_figure_using_telescope", "Stick_figure_spinning_globe_193", "Stick_figure_spinning_globe_anim", "Stick_figure_flips_globe", "Stick_figure_encasing_Earth", "Stick_figure_character_near_Earth", "Stick_figure_wearing_gas_mask", "Stick_figure_rejecting_science_icon", "Stick-figure-gentlemen-examining", "Stick_figure_transforming_coin", "Stick_figure_facing_city_skyline", "Stick_figure_facing_warning_tria", "Stick_figure_viewing_split_graphic", "Stick_meteorologist_examining_te", "Stick_scientist_pulling_electric", "Stick_figure_using_telescope", "Stick_figure_spinning_globe_193", "Stick_figure_flips_globe", "Stick_figure_encasing_Earth", "Stick_figure_character_near_Earth", "Stick_figure_wearing_gas_mask", "Stick-figure-gentlemen-examining", "Stick_figure_transforming_coin"],
 8: ["Stick_figure_near_wooden_bowl", "Stick_figure_crying", "Stick_figure_hat_on_ground", "Stick_figure_viewing_historical", "Stick_figure_tracking_world_map", "Stick_figure_connecting_glowing", "Stick_figure_holding_Earth", "Icons_appearing_over_Earth", "Stone_statue_melting_snow_rain", "Sprout_and_quill_pen_growing", "Farmer_stares_at_ruined_crops", "Stick_figure_farmer_dropping_to", "Stick_figure_near_dead_stalks", "Stick_figure_watching_withered_corn", "Exhausted_stick_figure", "Lone_farmhouse_in_New_Hampshire"],
}


def norm(s): return s.casefold().replace("…", "").replace("-", "_")

def act_for(stem):
 s=norm(stem)
 # Longest specific fragment first; the lists are editorial exceptions.
 matches=[(len(k), a) for a,keys in RULES.items() for k in keys if s.startswith(norm(k))]
 if matches: return max(matches)[1]
 terms={
  5:["frankenstein","villa","diodati","byron","mary","ohio","indiana","illinois","migration","westward","wagon","pioneer","quill","manuscript","poet","gothic","nightmare","storybook","lake_geneva","lakeside","book","frontier","compass_west"],
  6:["red_snow","crimson","monsoon","cholera","dry_fog","haze","fog","lightning","red_sky","chaotic","bizarre","town_square","proclamation"],
  3:["sulfur","sulphur","so2","aerosol","stratosphere","atmosphere","parasol","droplet","sunbeam","reflect","chemical","thermometer","anvil","light_beam"],
  2:["tambora","sumbawa","indonesia","eruption","erupt","volcano","magma","crater","pyroclastic","tsunami","ash_column","bamboo","bluebird","soldier","sailor","fish","island","soundwaves","mountain","lava","volcanic","ember","scorched"],
  4:["farmer","farm","field","corn","wheat","harvest","snow","winter","frost","cold","rain","flood","vermont","new_england","berkshire","stagecoach","withered","plow","weather","crop","ice","storm","wind","northeastern","european_ice","price","dead_stalk","diary"],
  7:["modern","city_skyline","scientist","satellite","greenhouse","technology","future","today","carbon","co2","population","toxic_gas","emergency","warning","energy","electric","science","globe","earth","map","temperature","split_graphic","comparison","telescope","monitor"],
  1:["june","calendar","coffee","bedroom","waking","sun_at_noon","clapperboard","hourglass","tavern_sign","town_sign","ink_curtain","spinning_clock"],
 }
 for a in (5,6,3,2,4,7,1):
  if any(t in s for t in terms[a]): return a
 return 8

def order_key(item, act):
 s=norm(item["stem"]); hints=ORDER[act]
 return (next((i for i,h in enumerate(hints) if h in s),len(hints)), s)

def ffmpeg_path(explicit=None):
 if explicit: return explicit
 p=shutil.which("ffmpeg")
 if p: return p
 try:
  import imageio_ffmpeg
  return imageio_ffmpeg.get_ffmpeg_exe()
 except Exception as exc:
  raise RuntimeError("FFmpeg not found. Install ffmpeg or imageio-ffmpeg.") from exc

def extract_assets(dest):
 dest.mkdir(parents=True,exist_ok=True); out=[]
 for zname in ZIPS:
  with zipfile.ZipFile(ROOT/zname) as zf:
   for info in zf.infolist():
    if not info.filename.lower().endswith((".jpg",".jpeg",".png")): continue
    name=Path(info.filename).name; p=dest/name
    if not p.exists() or p.stat().st_size!=info.file_size:
     with zf.open(info) as src,p.open("wb") as dst: shutil.copyfileobj(src,dst)
    out.append({"name":name,"stem":Path(name).stem,"path":p,"archive":zname,"act":act_for(Path(name).stem),"variation":0})
 if len(out)!=315 or len({x['name'] for x in out})!=len(out): raise RuntimeError(f"Expected 315 uniquely named images, got {len(out)}")
 return out

def curate(assets):
 groups={a:[] for a in ACTS}
 for x in assets: groups[x['act']].append(x)
 for a in groups:
  groups[a].sort(key=lambda x:order_key(x,a))
  clones=[]; counts=Counter()
  for prefix in REPRISES[a]:
   src=next((x for x in groups[a] if norm(x['stem']).startswith(norm(prefix))),None)
   if src is None: raise RuntimeError(f"Reprise source missing in act {a}: {prefix}")
   counts[src['name']]+=1; y=dict(src); y['variation']=counts[src['name']]; y['reprise']=True; clones.append(y)
  total=len(groups[a])+len(clones)
  slots={((i+1)*total)//(len(clones)+1):clones[i] for i in range(len(clones))}
  primary=iter(groups[a]); groups[a]=[slots[i] if i in slots else next(primary) for i in range(total)]
 return groups

def make_manifest(groups):
 shots=[]; chapters=[]; frame=0; num=1
 for a,items in groups.items():
  target=FRAMES[a]; n=len(items); durations=[target//n+(i<target%n) for i in range(n)]
  chapters.append({"act":a,"title":ACTS[a][0],"subtitle":ACTS[a][1],"start_frame":frame,"end_frame":frame+target,"frames":target})
  for x,d in zip(items,durations):
   shots.append({"scene":f"{num:03d}","act":a,"asset":x['name'],"archive":x['archive'],"variation":x.get('variation',0),"reprise":bool(x.get('reprise',False)),"start_frame":frame,"end_frame":frame+d,"duration_frames":d,"start_seconds":round(frame/FPS,3),"duration_seconds":round(d/FPS,3)})
   num+=1;frame+=d
 data={"title":"The Year Without a Summer","format":{"width":W,"height":H,"fps":FPS,"scene_count":len(shots),"unique_asset_count":len({s['asset'] for s in shots}),"reprise_count":sum(s['reprise'] for s in shots),"duration_frames":frame,"duration_seconds":round(frame/FPS,3)},"midroll_markers":["00:04:56","00:09:24","00:13:34"],"chapters":chapters,"scenes":shots}
 MANIFEST.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
 return data

def esc(s): return s.replace("\\","\\\\").replace(":","\\:").replace("'","\\'").replace(",","\\,")

def render_act(ff,act,items,dest,frames,crf,preset):
 n=len(items); total=frames+FADE*(n-1); q,r=divmod(total,n); lengths=[q+(i<r) for i in range(n)]
 cmd=[ff,"-y","-hide_banner","-loglevel","error"]
 for x in items: cmd += ["-loop","1","-framerate",str(FPS),"-i",str(x['path'])]
 filters=[];bold="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf";regular="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
 title,sub=ACTS[act]
 for i,length in enumerate(lengths):
  motion=(i+items[i].get('variation',0))%4
  z=f"1+0.03*on/{length}" if motion in (0,2) else f"1.03-0.03*on/{length}"
  xexpr=["(iw-iw/zoom)*0.18","(iw-iw/zoom)*0.82",f"(iw-iw/zoom)*on/{length}",f"(iw-iw/zoom)*(1-on/{length})"][motion]
  yexpr=["(ih-ih/zoom)*0.5","(ih-ih/zoom)*0.5","(ih-ih/zoom)*0.35","(ih-ih/zoom)*0.65"][motion]
  f=(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
     f"zoompan=z='{z}':x='{xexpr}':y='{yexpr}':d=1:s={W}x{H}:fps={FPS},"
     f"trim=end_frame={length},setpts=PTS-STARTPTS,settb=1/{FPS},format=yuv420p")
  if i==0:
   f+=(f",drawbox=x=48:y=538:w=900:h=132:color=black@0.62:t=fill:enable='lt(t,1.8)'"
       f",drawtext=fontfile={bold}:text='{act:02d} - {esc(title)}':x=72:y=560:fontsize=35:fontcolor=white:borderw=1:bordercolor=black@0.55:enable='lt(t,1.8)'"
       f",drawtext=fontfile={regular}:text='{esc(sub)}':x=74:y=610:fontsize=21:fontcolor=0xF4E6C2:borderw=1:bordercolor=black@0.45:enable='lt(t,1.8)'")
  if act==1 and i==0: f+=",fade=t=in:st=0:d=0.9"
  filters.append(f+f"[v{i}]")
 prev="v0";acc=lengths[0]
 for i in range(1,n):
  label=f"x{i}";off=(acc-FADE)/FPS
  filters.append(f"[{prev}][v{i}]xfade=transition=fade:duration={FADE/FPS:.6f}:offset={off:.6f}[{label}]")
  prev=label;acc+=lengths[i]-FADE
 if act==8: end=f"[{prev}]trim=end_frame={frames},fade=t=out:st={max(0,frames/FPS-1.2):.6f}:d=1.2,settb=1/{FPS},setpts=PTS-STARTPTS[vout]"
 else: end=f"[{prev}]trim=end_frame={frames},settb=1/{FPS},setpts=PTS-STARTPTS[vout]"
 cmd += ["-filter_complex",";".join(filters+[end]),"-map","[vout]","-an","-frames:v",str(frames),"-r",str(FPS),"-c:v","libx264","-preset",preset,"-tune","animation","-crf",str(crf),"-pix_fmt","yuv420p","-profile:v","high","-level:v","3.1","-g",str(FPS*2),"-keyint_min",str(FPS*2),"-sc_threshold","0","-video_track_timescale","24000","-movflags","+faststart",str(dest)]
 p=subprocess.run(cmd)
 if p.returncode: raise subprocess.CalledProcessError(p.returncode,cmd)

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--ffmpeg');ap.add_argument('--crf',type=int,default=31);ap.add_argument('--preset',default='medium');ap.add_argument('--plan-only',action='store_true');ap.add_argument('--output',type=Path,default=OUT);ap.add_argument('--work-dir',type=Path,default=WORK_DIR);args=ap.parse_args()
 assets=extract_assets(ASSET_DIR);groups=curate(assets);data=make_manifest(groups)
 print(f"Assets {len(assets)} | cuts {data['format']['scene_count']} | {data['format']['duration_seconds']}s")
 for a,x in groups.items(): print(f"Act {a}: {len(x)} cuts / {FRAMES[a]/FPS:.3f}s - {ACTS[a][0]}")
 if data['format']['scene_count']!=397 or data['format']['unique_asset_count']!=315 or data['format']['reprise_count']!=82: raise RuntimeError('Scene manifest does not match 397/315/82 roadmap plan')
 if args.plan_only:return
 ff=ffmpeg_path(args.ffmpeg);args.work_dir.mkdir(parents=True,exist_ok=True);segs=[]
 for a,x in groups.items():
  p=args.work_dir/f"act_{a:02d}.mp4";render_act(ff,a,x,p,FRAMES[a],args.crf,args.preset);segs.append(p)
 concat=args.work_dir/'segments.ffconcat';concat.write_text('ffconcat version 1.0\n'+'\n'.join(f"file '{p.as_posix()}'" for p in segs)+'\n')
 meta=args.work_dir/'chapters.ffmeta';lines=[';FFMETADATA1','title=The Year Without a Summer','artist=Edited from supplied narration and illustrations','comment=Mid-roll markers at 04:56, 09:24, and 13:34.']
 for c in data['chapters']:lines+=['','[CHAPTER]','TIMEBASE=1/24',f"START={c['start_frame']}",f"END={c['end_frame']}",f"title={c['act']:02d} - {c['title']}"]
 meta.write_text('\n'.join(lines)+'\n');args.output.parent.mkdir(parents=True,exist_ok=True)
 cmd=[ff,'-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-i',str(VOICE),'-f','ffmetadata','-i',str(meta),'-map','0:v:0','-map','1:a:0','-map_metadata','2','-map_chapters','2','-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,apad','-c:a','aac','-b:a','96k','-ac','1','-ar','48000','-t',str(data['format']['duration_seconds']),'-movflags','+faststart',str(args.output)]
 p=subprocess.run(cmd)
 if p.returncode: raise subprocess.CalledProcessError(p.returncode,cmd)
 print(f"Rendered {args.output} ({args.output.stat().st_size/1048576:.1f} MiB)")
if __name__=='__main__':main()
