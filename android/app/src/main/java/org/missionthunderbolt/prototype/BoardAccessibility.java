package org.missionthunderbolt.prototype;

import android.graphics.Rect;
import android.os.Bundle;
import android.view.MotionEvent;
import android.view.View;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityManager;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityNodeProvider;

/** Virtual read-only cells and explicit actions for the synthetic board. */
final class BoardAccessibility extends AccessibilityNodeProvider {
 interface Model {
  String[] rows();
  Rect bounds(int column,int row,int columns,int rows);
  void move(int dx,int dy);
  void waitTurn();
  void zoom(int direction);
 }
 private final View host;
 private final Model model;
 private int focused=View.NO_ID, hovered=View.NO_ID;
 BoardAccessibility(View host,Model model) {this.host=host;this.model=model;}
 private boolean valid(int id,String[] rows) {
  return rows.length>0 && rows[0].length()>0 && id>=1 && id<=rows.length*rows[0].length();
 }
 private Rect visibleBounds(int x,int y,String[] rows) {
  Rect bounds=model.bounds(x,y,rows[0].length(),rows.length),visible=new Rect();
  if(!host.getLocalVisibleRect(visible) || !bounds.intersect(visible))bounds.setEmpty();
  return bounds;
 }
 @Override public AccessibilityNodeInfo createAccessibilityNodeInfo(int id) {
  String[] rows=model.rows();
  if(id==View.NO_ID) {
   AccessibilityNodeInfo node=AccessibilityNodeInfo.obtain(host);
   host.onInitializeAccessibilityNodeInfo(node);
   if(rows.length>0) {
    node.setCollectionInfo(AccessibilityNodeInfo.CollectionInfo.obtain(rows.length,rows[0].length(),false));
    for(int y=0;y<rows.length;++y)for(int x=0;x<rows[y].length();++x)
     if(!visibleBounds(x,y,rows).isEmpty())node.addChild(host,1+y*rows[0].length()+x);
   }
   addActions(node);return node;
  }
  if(!valid(id,rows))return null;
  int width=rows[0].length(),x=(id-1)%width,y=(id-1)/width;
  char cell=rows[y].charAt(x);
  AccessibilityNodeInfo node=AccessibilityNodeInfo.obtain();
  node.setSource(host,id);node.setParent(host);node.setPackageName(host.getContext().getPackageName());
  node.setClassName("android.view.View");node.setEnabled(host.isEnabled());node.setFocusable(true);
  node.setContentDescription((cell=='@'?"Player":cell=='#'?"Wall":"Floor")+", column "+(x+1)+", row "+(y+1));
  node.setCollectionItemInfo(AccessibilityNodeInfo.CollectionItemInfo.obtain(y,1,x,1,false));
  Rect bounds=visibleBounds(x,y,rows);node.setBoundsInParent(bounds);
  node.setVisibleToUser(host.isShown() && !bounds.isEmpty());
  int[] location=new int[2];host.getLocationOnScreen(location);bounds.offset(location[0],location[1]);node.setBoundsInScreen(bounds);
  node.setAccessibilityFocused(focused==id);
  node.addAction(focused==id ? AccessibilityNodeInfo.ACTION_CLEAR_ACCESSIBILITY_FOCUS : AccessibilityNodeInfo.ACTION_ACCESSIBILITY_FOCUS);
  return node;
 }
 @Override public java.util.List<AccessibilityNodeInfo> findAccessibilityNodeInfosByText(String text,int id) {
  java.util.List<AccessibilityNodeInfo> result=new java.util.ArrayList<>();
  if(text==null || text.isEmpty())return result;
  String[] rows=model.rows();
  if(id!=View.NO_ID && !valid(id,rows))return result;
  String query=text.toLowerCase(java.util.Locale.ROOT);
  int first=id==View.NO_ID ? 1 : id,last=id==View.NO_ID ? rows.length*rows[0].length() : id;
  for(int cell=first;cell<=last;++cell) {
   AccessibilityNodeInfo node=createAccessibilityNodeInfo(cell);
   if(node.isVisibleToUser() && node.getContentDescription().toString().toLowerCase(java.util.Locale.ROOT).contains(query))result.add(node);
   else node.recycle();
  }
  return result;
 }
 private void addActions(AccessibilityNodeInfo node) {
  int[] ids={R.id.move_up,R.id.move_down,R.id.move_left,R.id.move_right,R.id.wait_turn,R.id.zoom_in,R.id.zoom_out,R.id.zoom_reset};
  String[] labels={"Move up","Move down","Move left","Move right","Wait one time unit","Zoom in","Zoom out","Show entire map"};
  for(int i=0;i<ids.length;++i)node.addAction(new AccessibilityNodeInfo.AccessibilityAction(ids[i],labels[i]));
 }
 boolean hostAction(int action) {
  if(action==R.id.move_up)model.move(0,-1);
  else if(action==R.id.move_down)model.move(0,1);
  else if(action==R.id.move_left)model.move(-1,0);
  else if(action==R.id.move_right)model.move(1,0);
  else if(action==R.id.wait_turn)model.waitTurn();
  else if(action==R.id.zoom_in)model.zoom(1);
  else if(action==R.id.zoom_out)model.zoom(-1);
  else if(action==R.id.zoom_reset)model.zoom(0);
  else return false;
  return true;
 }
 @Override public boolean performAction(int id,int action,Bundle arguments) {
  if(id==View.NO_ID)return host.performAccessibilityAction(action,arguments);
  if(!valid(id,model.rows()))return false;
  if(action==AccessibilityNodeInfo.ACTION_ACCESSIBILITY_FOCUS) {
   String[] rows=model.rows();int width=rows[0].length();
   if(focused==id || !host.isShown() || visibleBounds((id-1)%width,(id-1)/width,rows).isEmpty())return false;
   int old=focused;focused=id;
   if(old!=View.NO_ID)send(old,AccessibilityEvent.TYPE_VIEW_ACCESSIBILITY_FOCUS_CLEARED);
   send(id,AccessibilityEvent.TYPE_VIEW_ACCESSIBILITY_FOCUSED);return true;
  }
  if(action==AccessibilityNodeInfo.ACTION_CLEAR_ACCESSIBILITY_FOCUS && focused==id) {
   focused=View.NO_ID;send(id,AccessibilityEvent.TYPE_VIEW_ACCESSIBILITY_FOCUS_CLEARED);return true;
  }
  return false;
 }
 @Override public AccessibilityNodeInfo findFocus(int focus) {
  return focus==AccessibilityNodeInfo.FOCUS_ACCESSIBILITY && focused!=View.NO_ID ? createAccessibilityNodeInfo(focused) : null;
 }
 private void send(int id,int type) {
  if(host.getParent()==null)return;
  AccessibilityManager manager=(AccessibilityManager)host.getContext().getSystemService(android.content.Context.ACCESSIBILITY_SERVICE);
  if(!manager.isEnabled())return;
  AccessibilityEvent event=AccessibilityEvent.obtain(type);event.setSource(host,id);
  event.setPackageName(host.getContext().getPackageName());event.setClassName("android.view.View");
  host.getParent().requestSendAccessibilityEvent(host,event);
 }
 boolean hover(MotionEvent event) {
  AccessibilityManager manager=(AccessibilityManager)host.getContext().getSystemService(android.content.Context.ACCESSIBILITY_SERVICE);
  if(!manager.isEnabled() || !manager.isTouchExplorationEnabled())return false;
  int next=View.NO_ID;
  if(event.getActionMasked()!=MotionEvent.ACTION_HOVER_EXIT) {
   String[] rows=model.rows();
   for(int y=0;y<rows.length;++y)for(int x=0;x<rows[y].length();++x)
    if(visibleBounds(x,y,rows).contains((int)event.getX(),(int)event.getY()))next=1+y*rows[0].length()+x;
  }
  if(next!=hovered) {
   if(next!=View.NO_ID)send(next,AccessibilityEvent.TYPE_VIEW_HOVER_ENTER);
   if(hovered!=View.NO_ID)send(hovered,AccessibilityEvent.TYPE_VIEW_HOVER_EXIT);
   hovered=next;
  }
  return next!=View.NO_ID || event.getActionMasked()==MotionEvent.ACTION_HOVER_EXIT;
 }
 void changed() {
  if(focused!=View.NO_ID) {
   String[] rows=model.rows();int old=focused;
   if(!valid(old,rows) || visibleBounds((old-1)%rows[0].length(),(old-1)/rows[0].length(),rows).isEmpty()) {
    focused=View.NO_ID;send(old,AccessibilityEvent.TYPE_VIEW_ACCESSIBILITY_FOCUS_CLEARED);
   }
  }
  host.sendAccessibilityEvent(AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED);
 }
}
