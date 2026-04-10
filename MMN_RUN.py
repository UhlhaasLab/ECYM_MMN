"""
Passive auditory MMN with visual distraction (silent cartoon)

TO DO
- 2 simple comprehension questions after the run
"""
from psychopy import visual, core, event, sound, monitors
import csv, time, os

from MMN_init import (  SUB, SUB_DIR,
                        # triggers
                        TRIG_STD, TRIG_DDEV, 
                        TRIG_RUN_START, TRIG_RUN_END,
                        # vpixx
                        device, buttonCodes, myLog, stim_monitor,
                        # preload
                        preload_stim, preload_txt)

from utils.pixel_mode           import trigger_to_RGB, draw_pixel, print_trigger_info
from utils.buttons              import collect_response, flush_buttons
from utils.escape_cleanup_abort import check_abort, cleanup

# =================================================================
# TO BE CHANGED BY EXPERIMENTER FOR EACH RUN
# =================================================================
RUN = 1     # 1, then 2          
# =================================================================

# -------------------- GENERAL --------------------
#timestamp = time.strftime('%Y%m%d_%H%M%S') # this is only needed for logging. we dont need any logging here?
global_clock = core.Clock()

# -------------------- WINDOW --------------------
monitor_settings = stim_monitor()
# set fullscr to True in MSR
win = visual.Window(
    monitor=monitor_settings['monitor_name'], size=monitor_settings['monitor_size_pix'], 
    fullscr=True, 
    units="deg", 
    color=[211, 211, 211],
    colorSpace='rgb255', 
    #colorSpace='rgb',
    #colorSpace='rgb1',
    screen=monitor_settings["screen_number"]
)
win.mouseVisible = False
mouse = event.Mouse(visible=False)

# -------------------- PRELOAD STIMULI & TEXT --------------------
stim = preload_stim(win, RUN) # RUN passed to preload_stim
movie = stim["movie"]
std_sound = stim["std_sound"]
ddev_sound = stim["ddev_sound"]

txt = preload_txt(win)
instr = txt["txt_intro"]
txt_finished = txt["txt_finished"]

# -------------------- TRIAL LOADING --------------------
def load_trials():
    master_sequence_file = os.path.join(SUB_DIR, f"{SUB}_MMN_master_trial_sequence.csv")
    if not os.path.exists(master_sequence_file):
        raise FileNotFoundError(f"ERROR: Master sequence file not found for {SUB}!")
    with open(master_sequence_file, "r", encoding="utf-8") as f:
        all_trials = list(csv.DictReader(f))
    current_run_trials = [t for t in all_trials if int(t["run"]) == RUN]
    if not current_run_trials:
        raise ValueError(f"Could not find any trials for RUN {RUN} in the master file.")
    print(f"Successfully loaded {len(current_run_trials)} trials for RUN {RUN}.")
    return current_run_trials

trials = load_trials()

# ============================================================================================
# draw → win.flip() → device.updateRegisterCache() → read/debug
# -------------------- INSTRUCTIONS --------------------
instr.draw()
win.flip()
device.updateRegisterCache()

flush_buttons(device, myLog)

while True:
    button, _ = collect_response(device, myLog, buttonCodes)
    
    #if button in ["red", "green"]: #+++COMMENT IN AGAIN WHEN VPIXX
    if event.getKeys(keyList=['r','g','b']): # for keyboard testing: wait for any key press to start
        break
    if check_abort():
        core.quit()

# -------------------- COUNTDOWN --------------------
# for number in ["3", "2", "1"]:
#     countdown_text = visual.TextStim(win, text=number, height=3, color='black')
#     countdown_text.draw()
#     win.flip()
#     core.wait(1.0) # Show each number for 1 second

# -------------------- MAIN LOOP --------------------
movie.setAutoDraw(True)
movie.play()
global_clock.reset()

# 1. Show initial "Run Start" trigger (Analogous to Initial Fixation)
draw_pixel(win, trigger_to_RGB(TRIG_RUN_START))
win.flip()
core.wait(0.02)  # to let trigger pixel settle
device.updateRegisterCache()
print_trigger_info(device, TRIG_RUN_START)

SOA = 0.5
trial_idx = 0
next_sound_time = 0.0

print(f"Starting Run {RUN}...")

while trial_idx < len(trials):
    check_abort()

    current_time = global_clock.getTime()

    # --- 1. CHECK if it's time for a sound event ---
    if current_time >= next_sound_time:
        stim_info = trials[trial_idx]
        stim_type = stim_info['stim_type']

        # Map trial type to trigger
        if stim_type == "STD":
            current_trig = TRIG_STD
            sound_to_play = std_sound
        else: # DDEV
            current_trig = TRIG_DDEV
            sound_to_play = ddev_sound

        
        # --- 2. TRIGGER PRESENTATION
        # The movie is drawn automatically via setAutoDraw(True)
        draw_pixel(win, trigger_to_RGB(current_trig)) # Draw trigger pixel LAST

        # Sync sound and register cache timing to the flip
        win.callOnFlip(sound_to_play.play)
        
        win.flip() # Sound plays + Movie continues + Trigger appears
        
        core.wait(0.02) # to let trigger pixel settle (consistent with emotion exp)
        device.updateRegisterCache()
        print_trigger_info(device, current_trig)

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
core.wait(0.02) # to let trigger pixel settle
device.updateRegisterCache()
print_trigger_info(device, expected_trigger=TRIG_RUN_END)

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