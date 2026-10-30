package org.missionthunderbolt.prototype;

import android.test.ActivityInstrumentationTestCase2;
import android.widget.TextView;
import android.view.View;
import android.content.pm.ActivityInfo;

@SuppressWarnings("deprecation")
public class DemoActivityTest extends ActivityInstrumentationTestCase2<MainActivity> {
 public DemoActivityTest() { super(MainActivity.class); }
 @Override protected void setUp() throws Exception {
  super.setUp();
  // These legacy regressions deliberately exercise the original synthetic demo.
  // New mission behavior has its own IntegrationMissionTest coverage.
  MainActivity activity=getActivity();
  StringBuilder body=new StringBuilder("MTDEMO 0\n20 12 1 0 1 1\n");
  for(int y=0;y<12;++y) {
   for(int x=0;x<20;++x)body.append(y==0 || y==11 || x==0 || x==19?'#':'.');
   body.append('\n');
  }
  java.util.zip.CRC32 crc=new java.util.zip.CRC32();crc.update(body.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
  String fixture=body.toString()+String.format(java.util.Locale.ROOT,"CRC32 %08x\n",crc.getValue());
  java.lang.reflect.Method restore=MainActivity.class.getDeclaredMethod("restore",String.class);restore.setAccessible(true);
  assertTrue("Authored legacy fixture must restore",(Boolean)restore.invoke(null,fixture));
  java.lang.reflect.Method refresh=MainActivity.class.getDeclaredMethod("refresh");refresh.setAccessible(true);
  java.lang.reflect.Method persist=MainActivity.class.getDeclaredMethod("persistState");persist.setAccessible(true);
  java.lang.reflect.Field modern=MainActivity.class.getDeclaredField("modern"),zoom=MainActivity.class.getDeclaredField("zoom");
  modern.setAccessible(true);zoom.setAccessible(true);
  getInstrumentation().runOnMainSync(() -> {
   try {modern.setBoolean(activity,false);zoom.setFloat(activity,1f);refresh.invoke(activity);persist.invoke(activity);}
   catch(Exception error) {throw new AssertionError(error);}
  });
  getInstrumentation().waitForIdleSync();
 }

 private void click(final MainActivity activity, final int id) throws Throwable {
  runTestOnUiThread(() -> activity.findViewById(id).performClick()); getInstrumentation().waitForIdleSync();
 }
 private String status(MainActivity activity) { return ((TextView)activity.findViewById(R.id.status)).getText().toString(); }
 private void logRecreationActivity(String stage,MainActivity activity) {
  android.util.Log.i("MTRecreation",stage+" identity="+System.identityHashCode(activity)+
   " taskId="+activity.getTaskId()+
   " destroyed="+activity.isDestroyed()+" finishing="+activity.isFinishing()+
   " windowFocus="+activity.hasWindowFocus()+" attached="+activity.getWindow().getDecorView().isAttachedToWindow());
 }
 private MainActivity recreateAndAwait(MainActivity previous) throws Throwable {
  final int[] targetTask={-1};runTestOnUiThread(() -> targetTask[0]=previous.getTaskId());
  final java.util.concurrent.ArrayBlockingQueue<MainActivity> resumed=new java.util.concurrent.ArrayBlockingQueue<>(16);
  final java.util.concurrent.atomic.AtomicBoolean overflow=new java.util.concurrent.atomic.AtomicBoolean();
  android.app.Application application=previous.getApplication();
  android.app.Application.ActivityLifecycleCallbacks callbacks=new android.app.Application.ActivityLifecycleCallbacks() {
   public void onActivityCreated(android.app.Activity activity,android.os.Bundle state) {}
   public void onActivityStarted(android.app.Activity activity) {}
   public void onActivityResumed(android.app.Activity activity) {
    if(activity instanceof MainActivity && activity!=previous && activity.getTaskId()==targetTask[0]) {
     logRecreationActivity("resumed target",(MainActivity)activity);
     if(!resumed.offer((MainActivity)activity))overflow.set(true);
    }
   }
   public void onActivityPaused(android.app.Activity activity) {}
   public void onActivityStopped(android.app.Activity activity) {}
   public void onActivitySaveInstanceState(android.app.Activity activity,android.os.Bundle state) {}
   public void onActivityDestroyed(android.app.Activity activity) {}
  };
  try {
   runTestOnUiThread(() -> {
    application.registerActivityLifecycleCallbacks(callbacks);
    logRecreationActivity("request",previous);previous.recreate();
   });
   long deadline=android.os.SystemClock.uptimeMillis()+20000;
   while(android.os.SystemClock.uptimeMillis()<deadline) {
    assertFalse("Recreation resume queue overflow",overflow.get());
    MainActivity candidate=resumed.poll(Math.max(1,deadline-android.os.SystemClock.uptimeMillis()),java.util.concurrent.TimeUnit.MILLISECONDS);
    if(candidate==null)break;
    getInstrumentation().waitForIdleSync();boolean[] live={false};
    runTestOnUiThread(() -> {
     logRecreationActivity("previous",previous);logRecreationActivity("candidate",candidate);
     live[0]=candidate!=previous && !candidate.isDestroyed() && !candidate.isFinishing() && candidate.getTaskId()==targetTask[0];
    });
    assertFalse("Recreation resume queue overflow",overflow.get());
    if(live[0]) {setActivity(candidate);return candidate;}
   }
   assertFalse("Recreation resume queue overflow",overflow.get());
   fail("A distinct live activity was not recreated");return null;
  } finally {runTestOnUiThread(() -> application.unregisterActivityLifecycleCallbacks(callbacks));}
 }
 private void automaticPlacement(MainActivity activity) throws Throwable {
  for(int n=0;n<3 && !((android.widget.Button)activity.findViewById(R.id.controls_position)).getText().toString().equals("Controls: Auto");++n)click(activity,R.id.controls_position);
 }
 private void assertPlacement(MainActivity activity,int position) throws Throwable {
  java.util.concurrent.CountDownLatch laidOut=new java.util.concurrent.CountDownLatch(1);
  runTestOnUiThread(() -> {
   View root=activity.findViewById(R.id.layout_root);
   root.getViewTreeObserver().addOnPreDrawListener(new android.view.ViewTreeObserver.OnPreDrawListener() {
    public boolean onPreDraw() {root.getViewTreeObserver().removeOnPreDrawListener(this);laidOut.countDown();return true;}
   });root.requestLayout();root.invalidate();
  });
  boolean drawn=laidOut.await(10,java.util.concurrent.TimeUnit.SECONDS);
  StringBuilder state=new StringBuilder();
  runTestOnUiThread(() -> {
   View root=activity.findViewById(R.id.layout_root);
   state.append(" attached=").append(root.isAttachedToWindow()).append(" shown=").append(root.isShown())
    .append(" focus=").append(root.hasWindowFocus()).append(" width=").append(root.getWidth())
    .append(" visibility=").append(root.getWindowVisibility()).append(" destroyed=").append(activity.isDestroyed());
  });
  assertTrue("Control placement layout was not drawn:"+state,drawn);
  runTestOnUiThread(() -> {
   android.widget.LinearLayout root=activity.findViewById(R.id.layout_root),dpad=activity.findViewById(R.id.dpad);
   for(int n=0;n<dpad.getChildCount();++n) {
    android.view.ViewGroup row=(android.view.ViewGroup)dpad.getChildAt(n);
    View first=row.getChildAt(0),last=row.getChildAt(row.getChildCount()-1);
    int span=last.getRight()-first.getLeft(),free=row.getWidth()-row.getPaddingLeft()-row.getPaddingRight()-span;
    assertTrue(row.getWidth()>0 && span>0);
    int expected=row.getPaddingLeft()+(position==0?free/2:position==1?0:free);
    assertEquals("Directional row position",expected,first.getLeft());
   }
   if(root.getOrientation()==android.widget.LinearLayout.HORIZONTAL)
    assertEquals(position==1?R.id.control_panel:R.id.scene,root.getChildAt(0).getId());
   else assertEquals(R.id.scene,root.getChildAt(0).getId());
   android.widget.Button button=activity.findViewById(R.id.controls_position);
   assertTrue(button.getHeight()>=Math.round(48*activity.getResources().getDisplayMetrics().density));
   assertTrue(button.getContentDescription().toString().contains("Control placement"));
  });
 }
 public void testControlPlacementPreservesStateAndVisibility() throws Throwable {
  MainActivity a=getActivity();click(a,R.id.restart);click(a,R.id.move_right);automaticPlacement(a);
  if(a.findViewById(R.id.dpad).getVisibility()!=View.VISIBLE)click(a,R.id.controls);
  String before=status(a);assertPlacement(a,0);
  click(a,R.id.controls_position);assertEquals(before,status(a));assertPlacement(a,1);
  click(a,R.id.controls_position);assertEquals(before,status(a));assertPlacement(a,2);
  if(a.findViewById(R.id.dpad).getVisibility()==View.VISIBLE)click(a,R.id.controls);
  click(a,R.id.controls_position);assertEquals(View.GONE,a.findViewById(R.id.dpad).getVisibility());
  assertEquals(before,status(a));click(a,R.id.controls);assertPlacement(a,0);
 }
 public void testControlPlacementSurvivesRecreation() throws Throwable {
  MainActivity a=getActivity();click(a,R.id.restart);click(a,R.id.move_right);automaticPlacement(a);click(a,R.id.controls_position);
  if(a.findViewById(R.id.dpad).getVisibility()!=View.VISIBLE)click(a,R.id.controls);
  String before=status(a);MainActivity recreated=recreateAndAwait(a);
  assertNotNull(recreated);getInstrumentation().waitForIdleSync();assertEquals(before,status(recreated));
  assertEquals("Controls: Left",((android.widget.Button)recreated.findViewById(R.id.controls_position)).getText().toString());
  assertPlacement(recreated,1);automaticPlacement(recreated);
 }
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
  MainActivity recreated=recreateAndAwait(a);
  assertNotNull(recreated);getInstrumentation().waitForIdleSync();
  assertEquals(before,status(recreated));
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
 public void testAudioMemoryReleaseKeepsSettingsAndActiveState() throws Throwable {
  MainActivity a=getActivity();
  runTestOnUiThread(() -> {
   DemoAudio audio=new DemoAudio(a);
   try {
    audio.resume();audio.setEnabled(true);audio.setVolumePercent(37);
    assertTrue(audio.playCue());assertTrue(audio.hasTrack());int played=audio.getPlayCount();
    audio.trimMemory();audio.trimMemory();
    assertFalse(audio.hasTrack());assertEquals(0,audio.getConsumedFrames());
    assertTrue(audio.isEnabled());assertEquals(37,audio.getVolumePercent());assertFalse(audio.isUnavailable());
    assertEquals(played,audio.getPlayCount()); // Releasing memory must not replay a cue.
    assertTrue(audio.playCue());assertTrue(audio.hasTrack());assertEquals(played+1,audio.getPlayCount());
    audio.pause();audio.trimMemory();assertFalse(audio.playCue());assertFalse(audio.hasTrack());
    audio.resume();assertFalse(audio.hasTrack());assertEquals(played+1,audio.getPlayCount());
    assertTrue(audio.playCue());audio.close();audio.trimMemory();assertFalse(audio.playCue());assertFalse(audio.hasTrack());
   } finally {audio.close();}
  });
 }
 public void testActivityMemoryCallbacksPreserveCompleteState() throws Throwable {
  MainActivity a=getActivity();click(a,R.id.restart);click(a,R.id.move_right);
  java.lang.reflect.Field field=MainActivity.class.getDeclaredField("audio");field.setAccessible(true);
  DemoAudio audio=(DemoAudio)field.get(a);
  java.lang.reflect.Method snapshot=MainActivity.class.getDeclaredMethod("snapshot");snapshot.setAccessible(true);
  runTestOnUiThread(() -> {
   android.widget.Button toggle=a.findViewById(R.id.sound_toggle);
   if(toggle.getText().toString().equals("Sound: Off"))toggle.performClick();
   ((android.widget.SeekBar)a.findViewById(R.id.sound_volume)).setProgress(37);
  });
  String before=(String)snapshot.invoke(null),label=status(a);
  try {
   runTestOnUiThread(() -> {
    assertTrue(audio.playCue());
    a.onTrimMemory(android.content.ComponentCallbacks2.TRIM_MEMORY_RUNNING_MODERATE);
    assertTrue(audio.hasTrack()); // A hint below our release threshold keeps the cache.
   });
   for(int level:new int[]{android.content.ComponentCallbacks2.TRIM_MEMORY_RUNNING_LOW,
     android.content.ComponentCallbacks2.TRIM_MEMORY_RUNNING_CRITICAL,android.content.ComponentCallbacks2.TRIM_MEMORY_UI_HIDDEN,
     android.content.ComponentCallbacks2.TRIM_MEMORY_BACKGROUND,android.content.ComponentCallbacks2.TRIM_MEMORY_MODERATE,
     android.content.ComponentCallbacks2.TRIM_MEMORY_COMPLETE}) {
    runTestOnUiThread(() -> {
     assertTrue(audio.playCue());int played=audio.getPlayCount();a.onTrimMemory(level);
     assertFalse(audio.hasTrack());assertEquals(played,audio.getPlayCount());
     assertTrue(audio.isEnabled());assertEquals(37,audio.getVolumePercent());assertFalse(audio.isUnavailable());
    });
    assertEquals(before,(String)snapshot.invoke(null));assertEquals(label,status(a));
   }
   runTestOnUiThread(() -> {assertTrue(audio.playCue());a.onLowMemory();a.onLowMemory();assertFalse(audio.hasTrack());
    assertTrue(audio.playCue());assertTrue(audio.hasTrack());});
   assertEquals(before,(String)snapshot.invoke(null));assertEquals(label,status(a));
  } finally {
   runTestOnUiThread(() -> {android.widget.Button toggle=a.findViewById(R.id.sound_toggle);
    if(toggle.getText().toString().equals("Sound: On"))toggle.performClick();
    ((android.widget.SeekBar)a.findViewById(R.id.sound_volume)).setProgress(30);});
  }
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
  runTestOnUiThread(() -> {
   assertTrue("Activity window must receive the volume key",a.hasWindowFocus());
   assertTrue(a.findViewById(R.id.sound_volume).requestFocus());
   assertTrue("Volume slider must have focus before the key",a.findViewById(R.id.sound_volume).hasFocus());
  });
  getInstrumentation().sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_DPAD_RIGHT);getInstrumentation().waitForIdleSync();
  runTestOnUiThread(() -> {
   assertTrue("Activity window lost focus during the volume key",a.hasWindowFocus());
   assertTrue("Volume slider lost focus during the key",a.findViewById(R.id.sound_volume).hasFocus());
  });
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
  MainActivity recreated=recreateAndAwait(a);
  assertNotNull(recreated);getInstrumentation().waitForIdleSync();
  assertEquals("Sound: On",((android.widget.Button)recreated.findViewById(R.id.sound_toggle)).getText().toString());
  assertEquals(37,((android.widget.SeekBar)recreated.findViewById(R.id.sound_volume)).getProgress());
  assertTrue(status(recreated).contains("Turns: 0"));
  runTestOnUiThread(() -> {recreated.findViewById(R.id.sound_toggle).performClick();((android.widget.SeekBar)recreated.findViewById(R.id.sound_volume)).setProgress(30);});
 }

}
