package org.missionthunderbolt.prototype;
import android.app.Activity;
import android.os.Bundle;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.View;
import android.view.MotionEvent;
import android.view.KeyEvent;
import android.widget.LinearLayout;
import android.widget.Button;
import android.widget.TextView;

public class MainActivity extends Activity {
 static { System.loadLibrary("thunderbolt"); }
 private static native String map();
 private static native int move(int dx, int dy);
 private static native void reset();
 private boolean modern = false;
 private TextView status;
 private Board board;
 private int turns = 0;
 @Override public void onCreate(Bundle b) {
  super.onCreate(b);
  LinearLayout root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
  status = new TextView(this); status.setTextSize(17); status.setPadding(16,12,8,12); root.addView(status);
  board = new Board(); root.addView(board,new LinearLayout.LayoutParams(-1,0,1));
  LinearLayout tools = new LinearLayout(this);
  Button mode = new Button(this); mode.setText("Classic / Modern"); mode.setOnClickListener(v -> {modern = !modern; refresh();}); tools.addView(mode,new LinearLayout.LayoutParams(0,-2,1));
  Button restart = new Button(this); restart.setText("Restart"); restart.setOnClickListener(v -> {reset(); turns = 0; refresh();}); tools.addView(restart,new LinearLayout.LayoutParams(0,-2,1)); root.addView(tools);
  LinearLayout top = new LinearLayout(this); top.setGravity(android.view.Gravity.CENTER);
  top.addView(direction("UP",0,-1)); root.addView(top);
  LinearLayout bottom = new LinearLayout(this); bottom.setGravity(android.view.Gravity.CENTER);
  bottom.addView(direction("LEFT",-1,0)); bottom.addView(direction("DOWN",0,1)); bottom.addView(direction("RIGHT",1,0)); root.addView(bottom);
  setContentView(root); refresh();
 }
 private Button direction(String label,int dx,int dy) {Button b = new Button(this); b.setText(label); b.setOnClickListener(v -> step(dx,dy)); return b;}
 private void step(int dx,int dy) {turns = move(dx,dy); refresh();}
 private void refresh() {status.setText("Thunderbolt RESEARCH DEMO | " + (modern?"Modern":"Classic") + " | Turns: " + turns); board.invalidate();}
 @Override public boolean onKeyDown(int key,KeyEvent e) {switch(key) {
  case KeyEvent.KEYCODE_DPAD_UP: case KeyEvent.KEYCODE_W: step(0,-1);return true;
  case KeyEvent.KEYCODE_DPAD_DOWN: case KeyEvent.KEYCODE_S: step(0,1);return true;
  case KeyEvent.KEYCODE_DPAD_LEFT: case KeyEvent.KEYCODE_A: step(-1,0);return true;
  case KeyEvent.KEYCODE_DPAD_RIGHT: case KeyEvent.KEYCODE_D: step(1,0);return true;
 }return super.onKeyDown(key,e);}
 class Board extends View {
  final Paint p = new Paint(); Board(){super(MainActivity.this);p.setAntiAlias(false);}
  @Override protected void onDraw(Canvas c) {super.onDraw(c);String[] rows = map().split("\\n");if(rows.length==0)return;
   float cell = Math.min(getWidth()/(float)rows[0].length(),getHeight()/(float)rows.length);
   float x0 = (getWidth()-cell*rows[0].length())/2f, y0 = (getHeight()-cell*rows.length)/2f;
   c.drawColor(modern?Color.rgb(21,28,36):Color.WHITE);
   for(int y=0;y<rows.length;y++)for(int x=0;x<rows[y].length();x++){
    char ch=rows[y].charAt(x);
    int color=ch=='@'?(modern?Color.CYAN:Color.BLACK):ch=='#'?(modern?Color.rgb(95,115,132):Color.DKGRAY):(modern?Color.rgb(36,48,58):Color.LTGRAY);
    p.setColor(color);c.drawRect(x0+x*cell+1,y0+y*cell+1,x0+(x+1)*cell-1,y0+(y+1)*cell-1,p);
   }
  }
  @Override public boolean onTouchEvent(MotionEvent e) {if(e.getAction()!=MotionEvent.ACTION_UP)return true;
   float x=e.getX()-getWidth()/2f,y=e.getY()-getHeight()/2f;
   if(Math.abs(x)>Math.abs(y))step(x>0?1:-1,0);else step(0,y>0?1:-1);return true;
  }
 }
}
