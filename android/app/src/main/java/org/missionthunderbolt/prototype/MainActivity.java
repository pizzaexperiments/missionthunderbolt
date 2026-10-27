package org.missionthunderbolt.prototype;
import android.app.Activity;
import android.os.Bundle;
import android.util.AtomicFile;
import android.util.Log;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.View;
import android.view.MotionEvent;
import android.view.KeyEvent;
import android.view.ScaleGestureDetector;
import android.view.InputDevice;
import android.content.res.Configuration;
import android.widget.LinearLayout;
import android.widget.Button;
import android.widget.TextView;
import android.widget.ScrollView;
import android.widget.SeekBar;

public class MainActivity extends Activity {
 static { System.loadLibrary("thunderbolt"); }
 private static native String map();
 private static native int move(int dx, int dy);
 private static native void reset();
 private static native int turnCount();
 private static native int waitTurn();
 private static native boolean isModern();
 private static native void setModern(boolean enabled);
 private static native String snapshot();
 private static native boolean restore(String saved);
 private boolean modern = false;
 private TextView status;
 private Board board;
 private int turns = 0;
 private LinearLayout dpad;
 private LinearLayout root, scene;
 private ScrollView controlScroll;
 private Button placementToggle;
 private int controlPlacement = 0; // Automatic, left, right.
 private boolean controlsVisible = true;
 private float zoom = 1f;
 private int joystickX = 0, joystickY = 0;
 private DemoAudio audio;
 private Button soundToggle;
 private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
 @Override public void onCreate(Bundle b) {
  super.onCreate(b);
  restoreSavedState(b); modern = isModern();
  audio=new DemoAudio(this);
  audio.setEnabled(getPreferences(MODE_PRIVATE).getBoolean("sound_enabled",false));
  audio.setVolumePercent(getPreferences(MODE_PRIVATE).getInt("sound_volume",30));
  controlsVisible = getPreferences(MODE_PRIVATE).getBoolean("controls", true);
  controlPlacement = getPreferences(MODE_PRIVATE).getInt("controls_position",0);
  if(controlPlacement<0 || controlPlacement>2)controlPlacement=0;
  zoom = Math.max(1f, Math.min(4f, getPreferences(MODE_PRIVATE).getFloat("zoom", 1f)));
  boolean landscape = getResources().getConfiguration().orientation == Configuration.ORIENTATION_LANDSCAPE;
  root = new LinearLayout(this); root.setId(R.id.layout_root);
  root.setOrientation(landscape ? LinearLayout.HORIZONTAL : LinearLayout.VERTICAL);
  scene = new LinearLayout(this); scene.setId(R.id.scene); scene.setOrientation(LinearLayout.VERTICAL);
  status = new TextView(this); status.setId(R.id.status); status.setTextSize(17);
  status.setPadding(dp(12),dp(8),dp(8),dp(8)); scene.addView(status);
  board = new Board(); board.setId(R.id.board); scene.addView(board,new LinearLayout.LayoutParams(-1,0,1));
  root.addView(scene, landscape ? new LinearLayout.LayoutParams(0,-1,1) : new LinearLayout.LayoutParams(-1,0,1));
  LinearLayout controls = new LinearLayout(this); controls.setOrientation(LinearLayout.VERTICAL);
  LinearLayout tools = new LinearLayout(this); tools.setOrientation(landscape ? LinearLayout.VERTICAL : LinearLayout.HORIZONTAL);
  Button mode = button("Classic / Modern", R.id.mode);
  mode.setContentDescription("Switch presentation without restarting the demo");
  mode.setOnClickListener(v -> {modern = !modern; setModern(modern); refresh();});
  Button restart = button("Restart", R.id.restart);
  restart.setOnClickListener(v -> {reset(); setModern(modern); turns = 0; refresh();});
  Button toggle = button("Controls", R.id.controls);
  toggle.setContentDescription("Show or hide directional controls");
  toggle.setOnClickListener(v -> {controlsVisible = !controlsVisible; dpad.setVisibility(controlsVisible ? View.VISIBLE : View.GONE);});
  for (Button tool : new Button[]{mode,restart,toggle})
   tools.addView(tool,landscape ? new LinearLayout.LayoutParams(-1,-2) : new LinearLayout.LayoutParams(0,-2,1));
  controls.addView(tools);
  placementToggle=button("Controls: Auto",R.id.controls_position);
  placementToggle.setOnClickListener(v -> {
   controlPlacement=(controlPlacement+1)%3;
   getPreferences(MODE_PRIVATE).edit().putInt("controls_position",controlPlacement).apply();
   applyControlPlacement();
  });controls.addView(placementToggle);
  LinearLayout soundRow=new LinearLayout(this);soundRow.setGravity(android.view.Gravity.CENTER_VERTICAL);
  soundToggle=button("Sound: Off",R.id.sound_toggle);
  soundToggle.setOnClickListener(v -> {audio.setEnabled(!audio.isEnabled());refreshSound();});soundRow.addView(soundToggle);
  SeekBar volume=new SeekBar(this);volume.setId(R.id.sound_volume);volume.setMax(100);volume.setProgress(audio.getVolumePercent());volume.setMinimumHeight(dp(48));
  volume.setContentDescription("Demo sound volume "+audio.getVolumePercent()+" percent");
  volume.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
   public void onProgressChanged(SeekBar bar,int value,boolean fromUser) {audio.setVolumePercent(value);bar.setContentDescription("Demo sound volume "+value+" percent");}
   public void onStartTrackingTouch(SeekBar bar) {}
   public void onStopTrackingTouch(SeekBar bar) {}
  });
  soundRow.addView(volume,new LinearLayout.LayoutParams(0,dp(48),1));controls.addView(soundRow);
  refreshSound();
  dpad = new LinearLayout(this); dpad.setId(R.id.dpad); dpad.setOrientation(LinearLayout.VERTICAL);
  LinearLayout top = new LinearLayout(this); top.setGravity(android.view.Gravity.CENTER);
  top.addView(direction("UP",0,-1,R.id.move_up));
  Button wait = button("WAIT",R.id.wait_turn); wait.setContentDescription("Wait one time unit in place");
  wait.setOnClickListener(v -> waitAction()); top.addView(wait); dpad.addView(top);
  LinearLayout bottom = new LinearLayout(this); bottom.setGravity(android.view.Gravity.CENTER);
  bottom.addView(direction("LEFT",-1,0,R.id.move_left)); bottom.addView(direction("DOWN",0,1,R.id.move_down));
  bottom.addView(direction("RIGHT",1,0,R.id.move_right)); dpad.addView(bottom);
  dpad.setVisibility(controlsVisible ? View.VISIBLE : View.GONE); controls.addView(dpad);
  controlScroll = new ScrollView(this); controlScroll.setId(R.id.control_panel); controlScroll.setFillViewport(true); controlScroll.addView(controls);
  root.addView(controlScroll,landscape ? new LinearLayout.LayoutParams(-2,-1) : new LinearLayout.LayoutParams(-1,-2));
  applyControlPlacement();
  root.setOnApplyWindowInsetsListener((view,insets) -> {
   view.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),
    insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
   return insets.consumeSystemWindowInsets();
  });
  setContentView(root); board.requestFocus(); refresh();
 }
 private void applyControlPlacement() {
  if(root.getOrientation()==LinearLayout.HORIZONTAL)
   root.bringChildToFront(controlPlacement==1 ? scene : controlScroll);
  int gravity=controlPlacement==0 ? android.view.Gravity.CENTER_HORIZONTAL :
   controlPlacement==1 ? android.view.Gravity.LEFT : android.view.Gravity.RIGHT;
  gravity|=android.view.Gravity.CENTER_VERTICAL;
  for(int i=0;i<dpad.getChildCount();++i)((LinearLayout)dpad.getChildAt(i)).setGravity(gravity);
  String[] labels={"Auto","Left","Right"},names={"automatic","left","right"};
  placementToggle.setText("Controls: "+labels[controlPlacement]);
  placementToggle.setContentDescription("Control placement "+names[controlPlacement]+". Switch to "+names[(controlPlacement+1)%3]+" placement");
  root.requestLayout();root.invalidate();
 }
 private Button button(String label,int id) {
  Button b = new Button(this); b.setId(id); b.setText(label); b.setContentDescription(label);
  b.setMinWidth(dp(48)); b.setMinHeight(dp(48)); return b;
 }
 private Button direction(String label,int dx,int dy,int id) {
  Button b = button(label,id); b.setContentDescription("Move " + label.toLowerCase(java.util.Locale.ROOT));
  b.setOnClickListener(v -> step(dx,dy)); return b;
 }
 private void step(int dx,int dy) {int before=turns;turns=move(dx,dy);refresh();if(turns>before)playDemoCue();}
 private void waitAction() {int before=turns;turns=waitTurn();refresh();if(turns>before)playDemoCue();}
 private void playDemoCue() {audio.playCue();refreshSound();}
 private void refreshSound() {
  if(soundToggle==null)return;
  soundToggle.setText(audio.isUnavailable() ? "Sound unavailable" : audio.isEnabled() ? "Sound: On" : "Sound: Off");
  soundToggle.setContentDescription(audio.isUnavailable() ? "Demo sound unavailable" : audio.isEnabled() ? "Mute demo sound" : "Enable demo sound");
  soundToggle.setEnabled(!audio.isUnavailable());
 }
 private void refresh() {turns = turnCount(); status.setText("Thunderbolt RESEARCH DEMO | " + (modern?"Modern":"Classic") + " | Turns: " + turns); board.setContentDescription("Synthetic demo board. " + (modern ? "Modern" : "Classic") +
   " presentation. Turns " + turns + ". Use directional buttons or arrow keys to move."); board.invalidate(); board.accessibility.changed();}
 private AtomicFile saveFile() { return new AtomicFile(new File(getFilesDir(), "demo-state.mt")); }
 private void restoreSavedState(Bundle bundle) {
  if (bundle != null && restore(bundle.getString("demo-state"))) return;
  try (FileInputStream input = saveFile().openRead(); ByteArrayOutputStream data = new ByteArrayOutputStream()) {
   byte[] buffer = new byte[4096]; int count;
   while ((count = input.read(buffer)) != -1) {
    if (data.size() + count > 1024 * 1024) throw new IOException("Oversized demo save");
    data.write(buffer, 0, count);
   }
   if (!restore(new String(data.toByteArray(), StandardCharsets.UTF_8))) Log.w("Thunderbolt", "Invalid demo save ignored");
  } catch (java.io.FileNotFoundException expected) { /* New installation. */ }
    catch (IOException error) { Log.w("Thunderbolt", "Could not read demo save", error); }
 }
 private void persistState() {
  String data = snapshot(); if (data == null) return;
  AtomicFile file = saveFile(); FileOutputStream output = null;
  try {
   output = file.startWrite(); output.write(data.getBytes(StandardCharsets.UTF_8)); file.finishWrite(output);
  } catch (IOException error) {
   if (output != null) file.failWrite(output);
   Log.w("Thunderbolt", "Could not write demo save", error);
  }
 }
 @Override protected void onSaveInstanceState(Bundle state) {
  state.putString("demo-state", snapshot()); super.onSaveInstanceState(state);
 }
 @Override protected void onResume() {super.onResume();if(audio!=null)audio.resume();}
 @Override protected void onDestroy() {if(audio!=null)audio.close();super.onDestroy();}
 @Override protected void onPause() {
  persistState(); getPreferences(MODE_PRIVATE).edit().putBoolean("controls",controlsVisible).putFloat("zoom",zoom).apply();
  getPreferences(MODE_PRIVATE).edit().putBoolean("sound_enabled",audio.isEnabled()).putInt("sound_volume",audio.getVolumePercent()).apply();
  audio.pause();joystickX = joystickY = 0; super.onPause();
 }
 @Override public boolean dispatchKeyEvent(KeyEvent event) {
  if(getCurrentFocus() instanceof SeekBar && (event.getKeyCode()==KeyEvent.KEYCODE_DPAD_LEFT || event.getKeyCode()==KeyEvent.KEYCODE_DPAD_RIGHT))return super.dispatchKeyEvent(event);
  int dx=0,dy=0;
  switch(event.getKeyCode()) {
   case KeyEvent.KEYCODE_SPACE: case KeyEvent.KEYCODE_NUMPAD_5:
    if(event.getAction()==KeyEvent.ACTION_DOWN) waitAction();
    return true;
   case KeyEvent.KEYCODE_DPAD_UP: case KeyEvent.KEYCODE_W: dy=-1; break;
   case KeyEvent.KEYCODE_DPAD_DOWN: case KeyEvent.KEYCODE_S: dy=1; break;
   case KeyEvent.KEYCODE_DPAD_LEFT: case KeyEvent.KEYCODE_A: dx=-1; break;
   case KeyEvent.KEYCODE_DPAD_RIGHT: case KeyEvent.KEYCODE_D: dx=1; break;
   default: return super.dispatchKeyEvent(event);
  }
  if (event.getAction()==KeyEvent.ACTION_DOWN) step(dx,dy);
  return true;
 }
 @Override public boolean onGenericMotionEvent(MotionEvent event) {
  if ((event.getSource() & InputDevice.SOURCE_JOYSTICK) == InputDevice.SOURCE_JOYSTICK && event.getAction() == MotionEvent.ACTION_MOVE) {
   float x = event.getAxisValue(MotionEvent.AXIS_HAT_X), y = event.getAxisValue(MotionEvent.AXIS_HAT_Y);
   if (x == 0 && y == 0) { x = event.getAxisValue(MotionEvent.AXIS_X); y = event.getAxisValue(MotionEvent.AXIS_Y); }
   int dx = Math.abs(x) > .6f ? (x > 0 ? 1 : -1) : 0;
   int dy = Math.abs(y) > .6f ? (y > 0 ? 1 : -1) : 0;
   if ((dx != joystickX || dy != joystickY) && (dx != 0 || dy != 0)) {
    if (Math.abs(x) >= Math.abs(y)) step(dx,0); else step(0,dy);
   }
   joystickX=dx; joystickY=dy; return true;
  }
  return super.onGenericMotionEvent(event);
 }
 class Board extends View {
  final Paint p = new Paint();
  final ScaleGestureDetector scaler;
  final BoardAccessibility accessibility;
  boolean scaled = false;
  Board() {
   super(MainActivity.this); p.setAntiAlias(false); setFocusable(true); setFocusableInTouchMode(true);
   setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);
   accessibility=new BoardAccessibility(this,new BoardAccessibility.Model() {
    public String[] rows() {return map().split("\\n");}
    public android.graphics.Rect bounds(int x,int y,int columns,int rows) {return cellBounds(x,y,columns,rows);}
    public void move(int dx,int dy) {step(dx,dy);}
    public void waitTurn() {waitAction();}
    public void zoom(int direction) {
     zoom=direction==0 ? 1f : Math.max(1f,Math.min(4f,zoom*(direction>0 ? 1.25f : .8f)));
     invalidate(); accessibility.changed();
    }
   });
   scaler = new ScaleGestureDetector(MainActivity.this, new ScaleGestureDetector.SimpleOnScaleGestureListener() {
    @Override public boolean onScaleBegin(ScaleGestureDetector detector) { scaled=true; return true; }
    @Override public boolean onScale(ScaleGestureDetector detector) {
     zoom = Math.max(1f,Math.min(4f,zoom*detector.getScaleFactor())); invalidate(); accessibility.changed(); return true;
    }
   });
  }
  private android.graphics.Rect cellBounds(int x,int y,int columns,int rows) {
   if(rows==0 || columns==0)return new android.graphics.Rect();
   float cell=Math.max(1f,(float)Math.floor(Math.min(getWidth()/(float)columns,getHeight()/(float)rows)))*zoom;
   float x0=(getWidth()-cell*columns)/2f,y0=(getHeight()-cell*rows)/2f;
   return new android.graphics.Rect((int)Math.floor(x0+x*cell),(int)Math.floor(y0+y*cell),
    (int)Math.ceil(x0+(x+1)*cell),(int)Math.ceil(y0+(y+1)*cell));
  }
  @Override public android.view.accessibility.AccessibilityNodeProvider getAccessibilityNodeProvider() {return accessibility;}
  @Override public boolean performAccessibilityAction(int action,Bundle args) {
   return accessibility.hostAction(action) || super.performAccessibilityAction(action,args);
  }
  @Override public boolean dispatchHoverEvent(MotionEvent event) {return accessibility.hover(event) || super.dispatchHoverEvent(event);}
  @Override protected void onDraw(Canvas c) {super.onDraw(c);String[] rows = map().split("\\n");if(rows.length==0)return;
   float cell = Math.max(1f,(float)Math.floor(Math.min(getWidth()/(float)rows[0].length(),getHeight()/(float)rows.length)))*zoom;
   float x0 = (getWidth()-cell*rows[0].length())/2f, y0 = (getHeight()-cell*rows.length)/2f;
   c.drawColor(modern?Color.rgb(21,28,36):Color.WHITE);
   for(int y=0;y<rows.length;y++)for(int x=0;x<rows[y].length();x++){
    char ch=rows[y].charAt(x);
    int color=ch=='@'?(modern?Color.CYAN:Color.BLACK):ch=='#'?(modern?Color.rgb(95,115,132):Color.DKGRAY):(modern?Color.rgb(36,48,58):Color.LTGRAY);
    p.setColor(color);c.drawRect(x0+x*cell+1,y0+y*cell+1,x0+(x+1)*cell-1,y0+(y+1)*cell-1,p);
   }
  }
  @Override public boolean performClick() { super.performClick(); return true; }
  @Override public boolean onTouchEvent(MotionEvent event) {
   scaler.onTouchEvent(event);
   if (event.getActionMasked()==MotionEvent.ACTION_CANCEL) { scaled=false; return true; }
   if (event.getActionMasked()!=MotionEvent.ACTION_UP) return true;
   if (scaled) { scaled=false; return true; }
   performClick(); float x=event.getX()-getWidth()/2f, y=event.getY()-getHeight()/2f;
   if (Math.max(Math.abs(x),Math.abs(y))<dp(16)) return true;
   if (Math.abs(x)>Math.abs(y)) step(x>0?1:-1,0); else step(0,y>0?1:-1);
   return true;
  }
 }
}
