""" Passive auditory MMN with visual distraction (silent cartoon)

TO DO
- 2 simple comprehension questions after the run
- add core waits 0.016
- auditory stuff in init
- add pinkpanther 2 file if we choose that!

- tineke: should i store sound onset times to csv? or is trigger at sound onset enough?
sound_onset_psy = flip_marks["t_onset_psy"]
sound_onset_dev = flip_marks["t_onset_dev"]
- should i store anything to csv in MMN? no right`?

- move stuff to init

- should i load the movie to datapixx same as audio? no right as too big anyway
"""
from psychopy import visual, core, event, sound, monitors
import csv, time, os

from MMN_init import (  MRS, SUB, RUN, SUB_DIR, STIM_DIR, SOA,
                        # triggers
                        TRIG_STD, TRIG_DDEV, 
                        TRIG_RUN_START, TRIG_RUN_END,
                        # vpixx
                        device, buttonCodes, myLog, stim_monitor,
                        # preload
                        preload_stimuli, preload_txt)

from utils.pixel_mode           import pixel_time, trigger_to_RGB, draw_pixel, print_trigger_info
from utils.buttons              import collect_response, flush_buttons
from utils.escape_cleanup_abort import check_abort, cleanup

# -------------------- GENERAL --------------------
#timestamp = time.strftime('%Y%m%d_%H%M%S') # this is only needed for logging. we dont need any logging here?
psychopy_clock = core.Clock()

# -------------------- WINDOW --------------------
monitor_settings = stim_monitor()
# set fullscr to True in MSR
win = visual.Window(
    monitor=monitor_settings['monitor_name'], size=monitor_settings['monitor_size_pix'], 
    fullscr=True, 
    units="deg", 
    color=[212, 212, 212],
    colorSpace='rgb255', 
    #colorSpace='rgb',
    #colorSpace='rgb1',
    screen=monitor_settings["screen_number"]
)
win.mouseVisible = False
mouse = event.Mouse(visible=False)

# -------------------- PRELOAD TEXT & STIMULI --------------------
txt = preload_txt(win)
instr = txt["txt_intro"]
txt_finished = txt["txt_finished"]

stim = preload_stimuli(win, STIM_DIR, SUB_DIR, device, current_run=RUN, dB_SL=60)
# audio
audio_reg = stim["Audio"]
# visual 
movie = stim["movie"]

# -------------------- LOAD TRIALS --------------------
def load_trials():
    sequence_file = os.path.join(SUB_DIR, f"{SUB}_MMN_run{RUN}_trial_sequence.csv")
    if not os.path.exists(sequence_file):
        raise FileNotFoundError(f"ERROR: Sequence file not found for {SUB}!")
    with open(sequence_file, "r", encoding="utf-8") as f:
        all_trials = list(csv.DictReader(f))

    if not all_trials:
        raise ValueError(f"Could not find any trials in sequence file for RUN {RUN}.")

    print(f"Successfully loaded {len(all_trials)} trials (should be 640) for RUN {RUN}.")
    return all_trials

trials = load_trials()

# ============================================================================================
# -------------------- INSTRUCTIONS --------------------
instr.draw()
win.flip()
device.updateRegisterCache()

flush_buttons(device, myLog)

while True:
    button, _ = collect_response(device, myLog, buttonCodes)
    
    if button in ["red", "green"]:
    #if event.getKeys(keyList=['r','g','b']): # for keyboard testing: wait for any key press to start
        break
    if check_abort():
        core.quit()

# -------------------- COUNTDOWN --------------------
# for number in ["3", "2", "1"]:
#     countdown_text = visual.TextStim(win, text=number, height=3, color='black')
#     countdown_text.draw()
#     win.flip()
#     core.wait(1.0) # Show each number for 1 second
print(f"Starting RUN {RUN}...")

# -------------------- START MOVIE --------------------
movie.setAutoDraw(True)
movie.play()
psychopy_clock.reset()

draw_pixel(win, trigger_to_RGB(TRIG_RUN_START))

win.flip()
device.updateRegisterCache() # check erfan if pre or post wait

# debug
print(f"TRIG START ON {TRIG_RUN_START} = {trigger_to_RGB(TRIG_RUN_START)}")
print_trigger_info(device)
print("")

core.wait(pixel_time)  # to let trigger pixel settle

# debug
print(f"should still be: TRIG START ON {TRIG_RUN_START} = {trigger_to_RGB(TRIG_RUN_START)}")
print_trigger_info(device)
print("")

win.flip() # Movie continues + Trigger cleared

# debug
print(f"should still be gray background [212, 212, 212]")
print_trigger_info(device)
print("")

# -------------------- MAIN LOOP --------------------
# Initialize trial index and timing for the first sound
trial_idx = 0
next_sound_time = 0.0

while trial_idx < len(trials):
    check_abort()

    current_time = psychopy_clock.getTime()

    # --- 1. CHECK if it's time for a sound event ---
    if current_time >= next_sound_time:
        stim_info = trials[trial_idx]
        stim_type = stim_info['stim_type']

        # Map trial type to trigger
        if stim_type == "STD":
            current_trig = TRIG_STD
            sound_to_play = audio_reg['std_sound']
        else: # DDEV
            current_trig = TRIG_DDEV
            sound_to_play = audio_reg['ddev_sound']

        
        # --- 2. TRIGGER PRESENTATION
        # The movie is drawn automatically via setAutoDraw(True)
        # firt audio, then trigger pixel, then flip to present both together
            
        if MRS == 0:
            # AUDIO PSYCHOPY
            win.callOnFlip(sound_to_play.play)  # audio exactly on flip -> THIS WORKS IN PSYCHOPY
        
        if MRS == 1:
            # AUDIO VPIXX  -----------> ADAPT!!!!!!!!!!! make wihtout "if"?
            # prepare audio, not execute yet
            infoaud_fb = audio_reg
            device.audio.stopSchedule()
            device.audio.setAudioSchedule(0.0, infoaud_fb['fs'], infoaud_fb['n'], 'mono')
            device.audio.setReadAddress(infoaud_fb['addr'])
            device.audio.startSchedule()
            



        draw_pixel(win, trigger_to_RGB(current_trig)) # Draw trigger pixel LAST

        win.flip() # Sound plays + Movie continues + Trigger appears
        
        core.wait(pixel_time) # to let trigger pixel settle (consistent with emotion exp)
        device.updateRegisterCache()
        #print_trigger_info(device, current_trig)

        # --- 3. CLEAR TRIGGER ---
        win.flip() # Movie continues + Trigger cleared
        device.updateRegisterCache()

        # Update timing for the next sound
        next_sound_time += SOA
        trial_idx += 1

    else:
        # If it's not time for a sound, just keep the movie moving
        win.flip()

# -------------------- FINISH ---------------------
core.wait(SOA) # Wait for the final sound to finish playing
draw_pixel(win, trigger_to_RGB(TRIG_RUN_END)) # Send the RUN_END trigger
win.flip()
core.wait(pixel_time) # to let trigger pixel settle
device.updateRegisterCache()
# print_trigger_info(device, expected_trigger=TRIG_RUN_END)

print(f"Run {RUN} finished.")

# Stop movie, show finished message, and clean up
movie.stop()
movie.setAutoDraw(False)
txt_finished.draw()
win.flip()
core.wait(4)

cleanup()

device.din.stopDinLog()
device.updateRegisterCache()
device.close()
win.close()
core.quit()