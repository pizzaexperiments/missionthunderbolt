package org.missionthunderbolt.prototype;

import android.app.Instrumentation;
import android.test.ActivityInstrumentationTestCase2;
import android.widget.TextView;
import android.view.View;
import android.content.pm.ActivityInfo;

@SuppressWarnings("deprecation")
public class DemoActivityTest extends ActivityInstrumentationTestCase2<MainActivity> {
 public DemoActivityTest() { super(MainActivity.class); }
 private void click(final MainActivity activity, final int id) throws Throwable {
  runTestOnUiThread(() -> activity.findViewById(id).performClick()); getInstrumentation().waitForIdleSync();
 }
 private String status(MainActivity activity) { return ((TextView)activity.findViewById(R.id.status)).getText().toString(); }
 public void testModeKeepsTurnsAndRestartIsExplicit() throws Throwable {
  MainActivity a=getActivity(); click(a,R.id.restart); click(a,R.id.move_right);
  assertTrue(status(a).contains("Turns: 1"));
  click(a,R.id.mode); assertTrue(status(a).contains("Turns: 1"));
  click(a,R.id.restart); assertTrue(status(a).contains("Turns: 0"));
 }
 public void testAccessibleDirectionTargets() throws Throwable {
  MainActivity a=getActivity();
  for(int id:new int[]{R.id.move_up,R.id.move_down,R.id.move_left,R.id.move_right}) {
   View view=a.findViewById(id); assertNotNull(view.getContentDescription());
   int minimum=Math.round(48*a.getResources().getDisplayMetrics().density);
   assertTrue(view.getWidth()>=minimum); assertTrue(view.getHeight()>=minimum);
  }
 }
 public void testStateSurvivesRecreation() throws Throwable {
  MainActivity a=getActivity();click(a,R.id.restart);click(a,R.id.move_right);
  String before=status(a);
  Instrumentation.ActivityMonitor monitor=getInstrumentation().addMonitor(MainActivity.class.getName(),null,false);
  try {
   runTestOnUiThread(() -> a.recreate());
   MainActivity recreated=(MainActivity)monitor.waitForActivityWithTimeout(20000);
   assertNotNull(recreated);getInstrumentation().waitForIdleSync();
   assertEquals(before,status(recreated));
  } finally { getInstrumentation().removeMonitor(monitor); }
 }
 public void testKeyboardMovementWhenAButtonHasFocus() throws Throwable {
  MainActivity a=getActivity(); click(a,R.id.restart);
  runTestOnUiThread(() -> a.findViewById(R.id.mode).requestFocus());
  getInstrumentation().sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_DPAD_RIGHT);
  getInstrumentation().waitForIdleSync(); assertTrue(status(a).contains("Turns: 1"));
 }
 public void testJoystickHoldDoesNotRepeat() throws Throwable {
  MainActivity a=getActivity();click(a,R.id.restart);
  runTestOnUiThread(() -> {
   long now=android.os.SystemClock.uptimeMillis();
   android.view.MotionEvent event=android.view.MotionEvent.obtain(now,now,android.view.MotionEvent.ACTION_MOVE,1,0,0);
   event.setSource(android.view.InputDevice.SOURCE_JOYSTICK);
   a.onGenericMotionEvent(event);a.onGenericMotionEvent(event);event.recycle();
  });
  assertTrue(status(a).contains("Turns: 1"));
 }

 public void testFirstDirectionAfterTouchModeIsMovement() throws Throwable {
  MainActivity a=getActivity();click(a,R.id.restart);
  getInstrumentation().setInTouchMode(true);
  runTestOnUiThread(() -> a.findViewById(R.id.board).requestFocus());
  getInstrumentation().sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_DPAD_RIGHT);
  getInstrumentation().waitForIdleSync();assertTrue(status(a).contains("Turns: 1"));
 }

 public void testStatusFontUsesScaleAndReportsConfiguration() {
  MainActivity a=getActivity();TextView text=a.findViewById(R.id.status);
  assertEquals(17f*a.getResources().getDisplayMetrics().scaledDensity,text.getTextSize(),.5f);
  android.os.Bundle report=new android.os.Bundle();
  report.putString("stream","\nMT_CONFIG font_scale="+a.getResources().getConfiguration().fontScale+
   " orientation="+a.getResources().getConfiguration().orientation+" target_sdk="+a.getApplicationInfo().targetSdkVersion+"\n");
  getInstrumentation().sendStatus(0,report);
 }

 public void testManualWaitButtonAndSpaceAdvanceOneTurn() throws Throwable {
  MainActivity a=getActivity();click(a,R.id.restart);click(a,R.id.wait_turn);
  assertTrue(status(a).contains("Turns: 1"));
  getInstrumentation().sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_SPACE);
  getInstrumentation().waitForIdleSync();assertTrue(status(a).contains("Turns: 2"));
  click(a,R.id.mode);assertTrue(status(a).contains("Turns: 2"));
 }

 public void testVirtualMapHasCoordinatesAndReadOnlyFocus() throws Throwable {
  MainActivity a=getActivity();click(a,R.id.restart);
  runTestOnUiThread(() -> {
   View board=a.findViewById(R.id.board);
   android.view.accessibility.AccessibilityNodeProvider provider=board.getAccessibilityNodeProvider();assertNotNull(provider);
   assertTrue(board.performAccessibilityAction(R.id.zoom_reset,null));
   android.view.accessibility.AccessibilityNodeInfo root=provider.createAccessibilityNodeInfo(View.NO_ID);
   int columns=root.getCollectionInfo().getColumnCount(),rows=root.getCollectionInfo().getRowCount();
   assertEquals(columns*rows,root.getChildCount());root.recycle();
   android.view.accessibility.AccessibilityNodeInfo wall=provider.createAccessibilityNodeInfo(1);
   assertEquals("Wall, column 1, row 1",wall.getContentDescription().toString());wall.recycle();
   java.util.List<android.view.accessibility.AccessibilityNodeInfo> matches=provider.findAccessibilityNodeInfosByText("player",View.NO_ID);
   assertEquals(1,matches.size());matches.get(0).recycle();
   assertTrue(provider.findAccessibilityNodeInfosByText("player",0).isEmpty());
   int playerId=columns+2;
   android.view.accessibility.AccessibilityNodeInfo player=provider.createAccessibilityNodeInfo(playerId);
   assertEquals("Player, column 2, row 2",player.getContentDescription().toString());
   assertTrue(player.isVisibleToUser());player.recycle();
   assertTrue(provider.performAction(playerId,android.view.accessibility.AccessibilityNodeInfo.ACTION_ACCESSIBILITY_FOCUS,null));
   android.view.accessibility.AccessibilityNodeInfo focus=provider.findFocus(android.view.accessibility.AccessibilityNodeInfo.FOCUS_ACCESSIBILITY);
   assertNotNull(focus);assertTrue(focus.isAccessibilityFocused());focus.recycle();
   assertFalse(provider.performAction(playerId,android.view.accessibility.AccessibilityNodeInfo.ACTION_CLICK,null));
   assertTrue(provider.performAction(playerId,android.view.accessibility.AccessibilityNodeInfo.ACTION_CLEAR_ACCESSIBILITY_FOCUS,null));
   assertNull(provider.findFocus(android.view.accessibility.AccessibilityNodeInfo.FOCUS_ACCESSIBILITY));
   assertNull(provider.createAccessibilityNodeInfo(0));assertNull(provider.createAccessibilityNodeInfo(columns*rows+1));
   assertFalse(provider.performAction(0,android.view.accessibility.AccessibilityNodeInfo.ACTION_ACCESSIBILITY_FOCUS,null));
   assertTrue(status(a).contains("Turns: 0"));
  });
 }
 public void testAccessibleMapActionsShareWorldAcrossModes() throws Throwable {
  MainActivity a=getActivity();click(a,R.id.restart);
  runTestOnUiThread(() -> {
   View board=a.findViewById(R.id.board);
   android.view.accessibility.AccessibilityNodeProvider provider=board.getAccessibilityNodeProvider();
   android.view.accessibility.AccessibilityNodeInfo root=provider.createAccessibilityNodeInfo(View.NO_ID);
   int columns=root.getCollectionInfo().getColumnCount();
   java.util.Set<Integer> actions=new java.util.HashSet<>();
   for(android.view.accessibility.AccessibilityNodeInfo.AccessibilityAction action:root.getActionList())actions.add(action.getId());
   for(int id:new int[]{R.id.move_up,R.id.move_down,R.id.move_left,R.id.move_right,R.id.wait_turn,R.id.zoom_in,R.id.zoom_out,R.id.zoom_reset})assertTrue(actions.contains(id));
   root.recycle();
   assertTrue(board.performAccessibilityAction(R.id.move_right,null));assertTrue(status(a).contains("Turns: 1"));
   assertTrue(provider.performAction(View.NO_ID,R.id.wait_turn,null));assertTrue(status(a).contains("Turns: 2"));
   a.findViewById(R.id.mode).performClick();
   android.view.accessibility.AccessibilityNodeInfo player=provider.createAccessibilityNodeInfo(columns+3);
   assertEquals("Player, column 3, row 2",player.getContentDescription().toString());player.recycle();
   assertTrue(status(a).contains("Turns: 2"));
  });
 }
 public void testAccessibleZoomClipsCellsAndCanShowEntireMap() throws Throwable {
  MainActivity a=getActivity();click(a,R.id.restart);
  runTestOnUiThread(() -> {
   View board=a.findViewById(R.id.board);
   android.view.accessibility.AccessibilityNodeProvider provider=board.getAccessibilityNodeProvider();
   board.performAccessibilityAction(R.id.zoom_reset,null);
   android.view.accessibility.AccessibilityNodeInfo root=provider.createAccessibilityNodeInfo(View.NO_ID);
   int count=root.getChildCount();root.recycle();
   assertTrue(provider.performAction(1,android.view.accessibility.AccessibilityNodeInfo.ACTION_ACCESSIBILITY_FOCUS,null));
   for(int i=0;i<6;++i)board.performAccessibilityAction(R.id.zoom_in,null);
   assertNull(provider.findFocus(android.view.accessibility.AccessibilityNodeInfo.FOCUS_ACCESSIBILITY));
   assertFalse(provider.performAction(1,android.view.accessibility.AccessibilityNodeInfo.ACTION_ACCESSIBILITY_FOCUS,null));
   root=provider.createAccessibilityNodeInfo(View.NO_ID);assertTrue(root.getChildCount()<count);root.recycle();
   android.view.accessibility.AccessibilityNodeInfo corner=provider.createAccessibilityNodeInfo(1);
   assertFalse(corner.isVisibleToUser());android.graphics.Rect bounds=new android.graphics.Rect();corner.getBoundsInParent(bounds);
   assertTrue(bounds.isEmpty());corner.recycle();
   board.performAccessibilityAction(R.id.zoom_out,null);board.performAccessibilityAction(R.id.zoom_reset,null);
   root=provider.createAccessibilityNodeInfo(View.NO_ID);assertEquals(count,root.getChildCount());root.recycle();
   assertTrue(status(a).contains("Turns: 0"));
  });
 }

 private android.view.accessibility.AccessibilityNodeInfo findPlayer(android.view.accessibility.AccessibilityNodeInfo node) {
  if(node==null)return null;
  CharSequence description=node.getContentDescription();
  if(description!=null && description.toString().startsWith("Player, column"))return node;
  for(int i=0;i<node.getChildCount();++i) {
   android.view.accessibility.AccessibilityNodeInfo child=node.getChild(i);
   if(child==null)continue;
   android.view.accessibility.AccessibilityNodeInfo found=findPlayer(child);
   if(found!=null) {if(found!=child)child.recycle();return found;}
   child.recycle();
  }
  return null;
 }
 public void testFrameworkAccessibilityTreeExposesVirtualPlayer() throws Throwable {
  android.app.UiAutomation automation=getInstrumentation().getUiAutomation();
  MainActivity a=getActivity();click(a,R.id.restart);
  runTestOnUiThread(() -> a.findViewById(R.id.board).performAccessibilityAction(R.id.zoom_reset,null));
  getInstrumentation().waitForIdleSync();
  automation.waitForIdle(250,10000);
  android.view.accessibility.AccessibilityNodeInfo root=null;
  for(int retry=0;retry<50 && root==null;++retry) {
   root=automation.getRootInActiveWindow();
   if(root==null)android.os.SystemClock.sleep(100);
  }
  assertNotNull("Framework active window unavailable after accessibility connection",root);
  android.view.accessibility.AccessibilityNodeInfo player=findPlayer(root);
  assertNotNull("Virtual player must be reachable through the framework accessibility tree",player);
  assertEquals("Player, column 2, row 2",player.getContentDescription().toString());
  assertTrue(player.performAction(android.view.accessibility.AccessibilityNodeInfo.ACTION_ACCESSIBILITY_FOCUS));
  getInstrumentation().waitForIdleSync();assertTrue(status(a).contains("Turns: 0"));
  player.recycle();root.recycle();
 }

 public void testAudioTrackMuteVolumeFocusAndLifecycle() throws Throwable {
  MainActivity activity=getActivity();
  runTestOnUiThread(() -> {
   DemoAudio audio=new DemoAudio(activity);
   try {
    audio.resume();assertFalse(audio.playCue());assertFalse(audio.hasTrack());
    audio.setEnabled(true);audio.setVolumePercent(40);
    assertTrue("Authored PCM cue must initialize, write and start through AudioTrack",audio.playCue());
    assertTrue(audio.hasTrack());assertEquals(1,audio.getPlayCount());assertEquals(.4f,audio.getAppliedVolume(),.001f);
    for(int retry=0;retry<50 && audio.getConsumedFrames()==0;++retry)android.os.SystemClock.sleep(20);
    int consumed=audio.getConsumedFrames();assertTrue("Platform AudioTrack must consume authored PCM frames",consumed>0);
    android.os.Bundle report=new android.os.Bundle();report.putString("stream","\nMT_AUDIO consumed_frames="+consumed+" sample_rate=22050 authored_pcm=true\n");getInstrumentation().sendStatus(0,report);
    audio.onAudioFocusChange(android.media.AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK);
    assertEquals(.08f,audio.getAppliedVolume(),.001f);
    audio.onAudioFocusChange(android.media.AudioManager.AUDIOFOCUS_LOSS_TRANSIENT);
    audio.onAudioFocusChange(android.media.AudioManager.AUDIOFOCUS_GAIN);
    assertEquals(1,audio.getPlayCount());assertEquals(.4f,audio.getAppliedVolume(),.001f);
    audio.setVolumePercent(0);assertFalse(audio.playCue());
    audio.setVolumePercent(40);assertTrue(audio.playCue());assertEquals(2,audio.getPlayCount());
    audio.pause();assertFalse(audio.hasTrack());assertFalse(audio.playCue());
    audio.resume();assertEquals(2,audio.getPlayCount());
    audio.setEnabled(false);assertFalse(audio.playCue());assertEquals(0f,audio.getAppliedVolume(),.001f);
    audio.close();audio.close();assertFalse(audio.playCue());
   } finally {audio.close();}
   android.content.Context noAudio=new android.content.ContextWrapper(activity) {
    @Override public Object getSystemService(String name) {return android.content.Context.AUDIO_SERVICE.equals(name) ? null : super.getSystemService(name);}
   };
   DemoAudio silent=new DemoAudio(noAudio);silent.resume();silent.setEnabled(true);
   assertTrue(silent.isUnavailable());assertFalse(silent.playCue());assertFalse(silent.hasTrack());silent.close();
  });
 }
 public void testAudioControlsDoNotAdvanceTurns() throws Throwable {
  MainActivity a=getActivity();click(a,R.id.restart);
  runTestOnUiThread(() -> {
   android.widget.SeekBar volume=a.findViewById(R.id.sound_volume);
   assertTrue(volume.getHeight()>=Math.round(48*a.getResources().getDisplayMetrics().density));
   volume.setProgress(0);
   android.widget.Button toggle=a.findViewById(R.id.sound_toggle);
   if(toggle.getText().toString().equals("Sound: On"))toggle.performClick();
   toggle.performClick();assertEquals("Sound: On",toggle.getText().toString());
   assertTrue(status(a).contains("Turns: 0"));
   a.findViewById(R.id.wait_turn).performClick();assertTrue(status(a).contains("Turns: 1"));
   toggle.performClick();assertEquals("Sound: Off",toggle.getText().toString());
   assertTrue(status(a).contains("Turns: 1"));volume.setProgress(30);
   assertTrue(volume.getContentDescription().toString().contains("30 percent"));
  });
  getInstrumentation().setInTouchMode(false);
  runTestOnUiThread(() -> {assertTrue(a.findViewById(R.id.sound_volume).requestFocus());});
  getInstrumentation().sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_DPAD_RIGHT);getInstrumentation().waitForIdleSync();
  assertTrue(((android.widget.SeekBar)a.findViewById(R.id.sound_volume)).getProgress()>30);
  assertTrue(status(a).contains("Turns: 1"));
  runTestOnUiThread(() -> {((android.widget.SeekBar)a.findViewById(R.id.sound_volume)).setProgress(30);a.findViewById(R.id.board).requestFocus();});
 }
 public void testAudioPreferencesSurviveRecreation() throws Throwable {
  MainActivity a=getActivity();click(a,R.id.restart);
  runTestOnUiThread(() -> {
   android.widget.Button toggle=a.findViewById(R.id.sound_toggle);
   if(toggle.getText().toString().equals("Sound: Off"))toggle.performClick();
   ((android.widget.SeekBar)a.findViewById(R.id.sound_volume)).setProgress(37);
  });
  Instrumentation.ActivityMonitor monitor=getInstrumentation().addMonitor(MainActivity.class.getName(),null,false);
  try {
   runTestOnUiThread(() -> a.recreate());
   MainActivity recreated=(MainActivity)monitor.waitForActivityWithTimeout(20000);
   assertNotNull(recreated);getInstrumentation().waitForIdleSync();
   assertEquals("Sound: On",((android.widget.Button)recreated.findViewById(R.id.sound_toggle)).getText().toString());
   assertEquals(37,((android.widget.SeekBar)recreated.findViewById(R.id.sound_volume)).getProgress());
   assertTrue(status(recreated).contains("Turns: 0"));
   runTestOnUiThread(() -> {recreated.findViewById(R.id.sound_toggle).performClick();((android.widget.SeekBar)recreated.findViewById(R.id.sound_volume)).setProgress(30);});
  } finally {getInstrumentation().removeMonitor(monitor);}
 }

}
