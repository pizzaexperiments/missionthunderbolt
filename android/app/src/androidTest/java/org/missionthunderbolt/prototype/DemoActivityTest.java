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
}
