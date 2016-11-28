from Framework4.Control.Core.CObject import CObjectBase, Signal, Slot
import gevent
import time
import subprocess
import os
import math

class LimaPilatus(CObjectBase):
  def __init__(self, *args, **kwargs):
      CObjectBase.__init__(self, *args, **kwargs)

  def init(self):
      self.header = dict()

      #"/object/data[@name='uri']/@value"][0]
      pilatus_device = str(self.config["/object/data[@name='uri']/@value"][0])
      lima_device = str(self.config["/object/data[@name='lima_uri']/@value"][0])

      for channel_name in ("acq_status", "acq_trigger_mode", "saving_mode", "acq_nb_frames",
                           "acq_expo_time", "saving_directory", "saving_prefix",
                           "saving_suffix", "saving_next_number", "saving_index_format",
                           "saving_format", "saving_overwrite_policy",
                           "saving_header_delimiter", "last_image_saved"):
          self.addChannel("tango", channel_name, lima_device, channel_name)

      for channel_name in ("fill_mode", "working_energy", "threshold"):
          self.addChannel("tango", channel_name, pilatus_device, channel_name)

      self.addCommand("tango", "prepare_acq", lima_device, "prepareAcq")
      self.addCommand("tango",  "start_acq", lima_device, "startAcq")
      self.addCommand("tango", "stop_acq", lima_device, "stopAcq")
      self.addCommand("tango", "reset", lima_device, "reset")
      self.addCommand("tango", "set_image_header", lima_device, "SetImageHeader")

  def wait_ready(self):
      acq_status_chan = self.channels["acq_status"]
      with gevent.Timeout(10, RuntimeError("Detector not ready")):
          while acq_status_chan.value() != "Ready":
              time.sleep(1)

  def last_image_saved(self):
      return self.channels["last_image_saved"].value() + 1

  def get_deadtime(self):
      return 0 #float(self.config.getProperty("deadtime"))

  #@task
  def prepare_acquisition(self, exptime, number_of_images, comment, energy, bs_diode):
      self.header["file_comments"]=comment
      #self.header["N_oscillations"]=number_of_images
      #self.header["Oscillation_axis"]="omega"
      #self.header["Chi"]="0.0000 deg."
      #self.header["Phi"]="%0.4f deg." % diffractometer_positions.get("kappa_phi", -9999)
      #self.header["Kappa"]="%0.4f deg." % diffractometer_positions.get("kappa", -9999)
      #self.header["Alpha"]="0.0000 deg."
      #self.header["Polarization"]=self.collect_obj.bl_config.polarisation
      #self.header["Detector_2theta"]="0.0000 deg."
      #self.header["Angle_increment"]="%0.4f deg." % osc_range
      #self.header["Start_angle"]="%0.4f deg." % start
      #self.header["Transmission"]=self.collect_obj.get_transmission()
      #self.header["Flux"]=self.collect_obj.get_flux()
      #self.header["Beam_xy"]="(%.2f, %.2f) pixels" % tuple([value/0.172 for value in self.collect_obj.get_beam_centre()])
      #self.header["Detector_Voffset"]="0.0000 m"
      #self.header["Energy_range"]="(0, 0) eV"
      #self.header["Detector_distance"]="%f m" % (self.collect_obj.get_detector_distance()/1000.0)
      #self.header["Wavelength"]="%f A" % self.collect_obj.get_wavelength()
      #self.header["Trim_directory:"]="(nil)"
      #self.header["Flat_field:"]="(nil)"
      #self.header["Excluded_pixels:"]=" badpix_mask.tif"
      #self.header["N_excluded_pixels:"]="= 321"
      #self.header["Threshold_setting"]="%d eV" % self.getChannelObject("threshold").getValue()
      self.header["Flux"]=bs_diode
      self.header["Count_cutoff"]="1048500"
      self.header["Exposure_period"]="%f s" % (exptime+self.get_deadtime())
      self.header["Exposure_time"]="%f s" % exptime

      self.stop()
      self.wait_ready()

      self.set_energy_threshold(energy)

      self.channels["acq_trigger_mode"].set_value("EXTERNAL_TRIGGER_MULTI")
      
      self.channels["saving_mode"].set_value("AUTO_FRAME")
      self.channels["acq_nb_frames"].set_value(number_of_images)
      self.channels["acq_expo_time"].set_value(exptime)
      self.channels["saving_overwrite_policy"].set_value("OVERWRITE")

  def set_energy_threshold(self, energy):
      if energy is None:
          return  
      working_energy_chan = self.channels["working_energy"]
      working_energy = working_energy_chan.value()
      if math.fabs(working_energy - energy) > 0.1:
        working_energy_chan.setValue(energy)
        
        while math.fabs(working_energy_chan.getValue() - energy) > 0.1:
          time.sleep(1)    
      
      self.channels["fill_mode"].set_value("ON")
     
  #@task 
  def set_detector_filenames(self, filename, number_of_images):
      prefix, suffix = os.path.splitext(os.path.basename(filename))
      prefix = "_".join(prefix.split("_")[:-1])+"_"
      saving_directory = os.path.dirname(filename)
      
      subprocess.Popen("mkdir --parents %s" % saving_directory,
                                               shell=True, stdin=None, 
                                               stdout=None, stderr=None, 
                                               close_fds=True).wait()
      
      self.wait_ready()  
  
      self.channels["saving_directory"].set_value(saving_directory) 
      self.channels["saving_prefix"].set_value(prefix)
      self.channels["saving_suffix"].set_value(suffix)
      self.channels["saving_next_number"].set_value(1)
      self.channels["saving_index_format"].set_value("%05d")
      self.channels["saving_format"].set_value("EDF")
      self.channels["saving_header_delimiter"].set_value(["|", ";", ":"])

      headers = list()
      for i in range(number_of_images):
          header = "\n%s\n" % str(self.config["/object/data[@name='serial']/@value"][0])
          header += "# %s\n" % time.strftime("%Y/%b/%d %T")
          header += "# Pixel_size 172e-6 m x 172e-6 m\n"
          header += "# Silicon sensor, thickness 0.000320 m\n"  
          #self.header["Start_angle"]=start_angle
          for key, value in self.header.iteritems():
              header += "# %s %s\n" % (key, value)
          headers.append("%d : array_data/header_contents|%s;" % (i, header))    
      
      self.commands["set_image_header"](headers)
       
  #@task 
  def start_acquisition(self):
      self.commands["prepare_acq"]()
      return self.commands["start_acq"]()

  def stop(self):
      try:
          self.commands["stop_acq"]()
      except:
          pass
      time.sleep(1)
      self.commands["reset"]()



