package org.missionthunderbolt.prototype;

import android.app.Activity;
import android.app.Application;
import android.os.Bundle;
import android.test.ActivityInstrumentationTestCase2;
import android.view.View;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityNodeProvider;
import android.widget.TextView;

/** Visible mission behavior is separate from the legacy demo regressions. */
@SuppressWarnings("deprecation")
public class IntegrationMissionTest extends ActivityInstrumentationTestCase2<MainActivity> {
 public IntegrationMissionTest() {super(MainActivity.class);}
 private void click(MainActivity activity,int id) throws Throwable {
  runTestOnUiThread(() -> activity.findViewById(id).performClick());getInstrumentation().waitForIdleSync();
 }
 private String status(MainActivity activity) {return ((TextView)activity.findViewById(R.id.status)).getText().toString();}
 private static Object nativeValue(String name) throws Exception {
  java.lang.reflect.Method method=MainActivity.class.getDeclaredMethod(name);method.setAccessible(true);return method.invoke(null);
 }
 private void begin(MainActivity activity) throws Throwable {
  click(activity,R.id.new_mission);
  assertTrue((Boolean)nativeValue("isResearchMission"));assertTrue(status(activity).contains("RESEARCH MISSION"));
  assertTrue(status(activity).contains("Seed: "));assertTrue(status(activity).contains("Inventory: 0"));
  runTestOnUiThread(() -> activity.findViewById(R.id.board).performAccessibilityAction(R.id.zoom_reset,null));
  getInstrumentation().waitForIdleSync();
 }
 private MainActivity recreate(MainActivity previous) throws Throwable {
  final int task=previous.getTaskId();
  java.util.concurrent.ArrayBlockingQueue<MainActivity> resumed=new java.util.concurrent.ArrayBlockingQueue<>(16);
  java.util.concurrent.atomic.AtomicBoolean overflow=new java.util.concurrent.atomic.AtomicBoolean();
  Application application=previous.getApplication();
  Application.ActivityLifecycleCallbacks callbacks=new Application.ActivityLifecycleCallbacks() {
   public void onActivityResumed(Activity a) {
    if(a instanceof MainActivity && a!=previous && a.getTaskId()==task && !resumed.offer((MainActivity)a))overflow.set(true);
   }
   public void onActivityCreated(Activity a,Bundle b) {}
   public void onActivityStarted(Activity a) {}
   public void onActivityPaused(Activity a) {}
   public void onActivityStopped(Activity a) {}
   public void onActivitySaveInstanceState(Activity a,Bundle b) {}
   public void onActivityDestroyed(Activity a) {}
  };
  application.registerActivityLifecycleCallbacks(callbacks);
  try {
   runTestOnUiThread(() -> previous.recreate());long deadline=android.os.SystemClock.uptimeMillis()+20000;
   while(android.os.SystemClock.uptimeMillis()<deadline) {
    MainActivity candidate=resumed.poll(Math.max(1,deadline-android.os.SystemClock.uptimeMillis()),java.util.concurrent.TimeUnit.MILLISECONDS);
    if(candidate==null)break;getInstrumentation().waitForIdleSync();boolean[] live={false};
    runTestOnUiThread(() -> live[0]=!candidate.isDestroyed() && !candidate.isFinishing() && candidate.hasWindowFocus());
    assertFalse("Lifecycle queue overflow",overflow.get());
    if(live[0]) {setActivity(candidate);return candidate;}
   }
   fail("Mission activity must recreate into a distinct live focused instance");return null;
  } finally {application.unregisterActivityLifecycleCallbacks(callbacks);}
 }
 public void testNewMissionMapAndPickupAreVisible() throws Throwable {
  MainActivity a=getActivity();View action=a.findViewById(R.id.new_mission);assertNotNull(action);
  assertTrue(action.getHeight()>=Math.round(48*a.getResources().getDisplayMetrics().density));begin(a);
  View board=a.findViewById(R.id.board);AccessibilityNodeProvider provider=board.getAccessibilityNodeProvider();
  runTestOnUiThread(() -> {
   AccessibilityNodeInfo root=provider.createAccessibilityNodeInfo(View.NO_ID);
   assertEquals(67,root.getCollectionInfo().getColumnCount());assertEquals(19,root.getCollectionInfo().getRowCount());root.recycle();
   AccessibilityNodeInfo item=provider.createAccessibilityNodeInfo(67+4);
   assertEquals("Item, column 4, row 2",item.getContentDescription().toString());assertTrue(item.isVisibleToUser());item.recycle();
  });
  click(a,R.id.move_right);click(a,R.id.move_right);click(a,R.id.pickup);
  assertEquals(1,((Integer)nativeValue("inventoryCount")).intValue());assertTrue(status(a).contains("Inventory: 1"));
  assertTrue(status(a).contains("Turns: 3"));
  assertEquals(67,((String)nativeValue("map")).split("\\n")[0].length());
 }
 public void testMissionRecreationAndRestartPreserveModeAndSeed() throws Throwable {
  MainActivity a=getActivity();begin(a);int seed=(Integer)nativeValue("missionSeed");
  click(a,R.id.move_right);click(a,R.id.move_right);click(a,R.id.pickup);click(a,R.id.mode);
  boolean modern=(Boolean)nativeValue("isModern");String before=status(a);
  a=recreate(a);assertEquals(before,status(a));assertEquals(1,((Integer)nativeValue("inventoryCount")).intValue());
  click(a,R.id.restart);assertTrue((Boolean)nativeValue("isResearchMission"));
  assertEquals(seed,((Integer)nativeValue("missionSeed")).intValue());assertEquals(modern,((Boolean)nativeValue("isModern")).booleanValue());
  assertTrue(status(a).contains("Inventory: 0"));assertTrue(status(a).contains("Turns: 0"));
  assertTrue(((String)nativeValue("map")).contains("!"));
 }
 public void testZoomCameraAndAccessiblePickupShareMission() throws Throwable {
  MainActivity a=getActivity();begin(a);View board=a.findViewById(R.id.board);
  runTestOnUiThread(() -> {
   AccessibilityNodeProvider provider=board.getAccessibilityNodeProvider();
   AccessibilityNodeInfo whole=provider.createAccessibilityNodeInfo(View.NO_ID);int count=whole.getChildCount();whole.recycle();
   for(int i=0;i<6;++i)assertTrue(board.performAccessibilityAction(R.id.zoom_in,null));
   AccessibilityNodeInfo zoomed=provider.createAccessibilityNodeInfo(View.NO_ID);
   assertTrue("Zoom must clip the map",zoomed.getChildCount()<count);zoomed.recycle();
   AccessibilityNodeInfo player=provider.createAccessibilityNodeInfo(67+2);
   assertTrue("Camera must keep the player visible at mission zoom",player.isVisibleToUser());
   android.graphics.Rect bounds=new android.graphics.Rect();player.getBoundsInParent(bounds);assertFalse(bounds.isEmpty());player.recycle();
   assertTrue(board.performAccessibilityAction(R.id.move_right,null));assertTrue(board.performAccessibilityAction(R.id.move_right,null));
   assertTrue(board.performAccessibilityAction(R.id.pickup,null));
  });
  assertEquals(1,((Integer)nativeValue("inventoryCount")).intValue());assertTrue(status(a).contains("Inventory: 1"));
 }
}
