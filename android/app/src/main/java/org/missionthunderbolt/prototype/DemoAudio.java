package org.missionthunderbolt.prototype;

import android.content.Context;
import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;

/** Opt-in authored PCM cue. Historical samples and cue mappings are not packaged. */
@SuppressWarnings("deprecation")
final class DemoAudio implements AudioManager.OnAudioFocusChangeListener {
 private static final int RATE=22050,DURATION_MS=80;
 private final AudioManager manager;
 private final Handler handler=new Handler(Looper.getMainLooper());
 private final Runnable finish=() -> stopAndAbandon();
 private AudioTrack track;
 private boolean enabled=false,active=false,unavailable=false,closed=false;
 private int volumePercent=30,playCount=0;
 private float duck=1f,appliedVolume=0;
 DemoAudio(Context context) {manager=(AudioManager)context.getSystemService(Context.AUDIO_SERVICE);unavailable=manager==null;}
 synchronized boolean isEnabled() {return enabled;}
 synchronized boolean isUnavailable() {return unavailable;}
 synchronized boolean hasTrack() {return track!=null && track.getState()==AudioTrack.STATE_INITIALIZED;}
 synchronized int getVolumePercent() {return volumePercent;}
 synchronized int getPlayCount() {return playCount;}
 synchronized int getConsumedFrames() {return track==null ? 0 : track.getPlaybackHeadPosition();}
 synchronized float getAppliedVolume() {return appliedVolume;}
 synchronized void setEnabled(boolean value) {enabled=value;if(!value) {stopAndAbandon();releaseTrack();}applyVolume();}
 synchronized void setVolumePercent(int value) {
  volumePercent=Math.max(0,Math.min(100,value));
  if(volumePercent==0)stopAndAbandon();
  applyVolume();
 }
 synchronized void resume() {if(!closed)active=true;}
 synchronized void pause() {active=false;stopAndAbandon();releaseTrack();}
 synchronized void close() {pause();closed=true;}
 synchronized boolean playCue() {
  if(!enabled || !active || closed || unavailable || volumePercent==0 || manager==null)return false;
  try {
   if(manager.requestAudioFocus(this,AudioManager.STREAM_MUSIC,AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)!=AudioManager.AUDIOFOCUS_REQUEST_GRANTED)return false;
   if(track==null) {
    short[] samples=cue();
    track=new AudioTrack(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build(),
     new AudioFormat.Builder().setEncoding(AudioFormat.ENCODING_PCM_16BIT).setSampleRate(RATE).setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build(),
     samples.length*2,AudioTrack.MODE_STATIC,AudioManager.AUDIO_SESSION_ID_GENERATE);
    if(track.getState()==AudioTrack.STATE_UNINITIALIZED)throw new IllegalStateException("PCM output unavailable");
    int written=track.write(samples,0,samples.length);
    if(written!=samples.length || track.getState()!=AudioTrack.STATE_INITIALIZED)
     throw new IllegalStateException("PCM load failed: "+written+" of "+samples.length);
   }
   handler.removeCallbacks(finish);track.pause();
   if(track.setPlaybackHeadPosition(0)!=AudioTrack.SUCCESS)throw new IllegalStateException("Cannot restart PCM cue");
   duck=1f;applyVolume();
   if(unavailable)return false;
   track.play();playCount++;handler.postDelayed(finish,DURATION_MS+50);return true;
  } catch(RuntimeException error) {fail(error);return false;}
 }
 private static short[] cue() {
  short[] samples=new short[RATE*DURATION_MS/1000];
  for(int i=0;i<samples.length;++i) {
   double envelope=Math.min(1.0,Math.min(i/(RATE*.005),(samples.length-1-i)/(RATE*.01)));
   samples[i]=(short)(Math.sin(2*Math.PI*660*i/RATE)*7000*envelope);
  }
  return samples;
 }
 private synchronized void applyVolume() {
  appliedVolume=(enabled ? volumePercent/100f : 0f)*duck;
  if(track==null)return;
  try {if(track.setVolume(appliedVolume)!=AudioTrack.SUCCESS)throw new IllegalStateException("Cannot apply audio volume");}
  catch(RuntimeException error) {fail(error);}
 }
 @Override public synchronized void onAudioFocusChange(int change) {
  if(closed)return;
  if(change==AudioManager.AUDIOFOCUS_LOSS || change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT)stopAndAbandon();
  else if(change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK) {duck=.2f;applyVolume();}
  else if(change==AudioManager.AUDIOFOCUS_GAIN) {duck=1f;applyVolume();}
 }
 private synchronized void stopAndAbandon() {
  handler.removeCallbacks(finish);
  if(track!=null)try {track.pause();track.setPlaybackHeadPosition(0);} catch(RuntimeException error) {releaseTrack();}
  if(manager!=null)try {manager.abandonAudioFocus(this);} catch(RuntimeException ignored) { /* silent fallback */ }
 }
 private void releaseTrack() {
  if(track!=null) {try {track.release();} catch(RuntimeException ignored) { /* silent fallback */ }track=null;}
 }
 private void fail(RuntimeException error) {
  unavailable=true;stopAndAbandon();releaseTrack();Log.w("Thunderbolt","Demo audio unavailable; continuing silently",error);
 }
}
