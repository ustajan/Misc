#!/usr/bin/env python
# coding: utf-8

# In[ ]:


'''
Author:  Areg Danagoulian
AI engine:  ChatGPT o1-preview
date: 09.16.2024
License: see README

This code takes a version 2005 N42 file, parses it, extracts
 - the spectrum
 - calib parameters
 - live and real times
 - info on the instrument
and plots the spectrum 

Usage:  see usage example in the next cell
'''

import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np
import re


def instrument_information(root,ns_uri):
    instrument_info = root.find('.//' + ns_uri + 'InstrumentInformation')
    if instrument_info is None:
        # Try without namespace
        instrument_info = root.find('.//InstrumentInformation')

    if instrument_info is not None:
        # Try finding child elements with namespace
        instrument_type_elem = instrument_info.find(ns_uri + 'InstrumentType')
        manufacturer_elem = instrument_info.find(ns_uri + 'Manufacturer')

        # If not found, try without namespace
        if instrument_type_elem is None:
            instrument_type_elem = instrument_info.find('InstrumentType')
        if manufacturer_elem is None:
            manufacturer_elem = instrument_info.find('Manufacturer')

        instrument_type = instrument_type_elem.text.strip() if instrument_type_elem is not None else 'N/A'
        manufacturer = manufacturer_elem.text.strip() if manufacturer_elem is not None else 'N/A'

        print('Instrument Information:')
        print(f'  InstrumentType: {instrument_type}')
        print(f'  Manufacturer: {manufacturer}')
    else:
        print('No InstrumentInformation element found.')
    return


def decompress_counted_zeros(data):
    decompressed = []
    i = 0
    while i < len(data):
        value = data[i]
        if value != 0:
            decompressed.append(value)
            i += 1
        else:
            if i + 1 < len(data):
                zeros_count = data[i + 1]
                if zeros_count < 0:
                    raise ValueError("Invalid zeros count: cannot be negative")
                decompressed.extend([0] * zeros_count)
                i += 2
            else:
                raise ValueError("Invalid compression format: zero at end without count")
    return decompressed

def parse_n42_file(file_path):
    with open(file_path, 'r', encoding='utf-16') as f:
        xml_content = f.read()

    root = ET.fromstring(xml_content)
    namespace_uri = root.tag[root.tag.find("{")+1 : root.tag.find("}")]
    ns_uri = '{' + namespace_uri + '}'

    instrument_information(root,ns_uri)
    measurements = root.findall('.//' + ns_uri + 'Measurement')
    if not measurements:
        print('No Measurement elements found.')
    for measurement in measurements:
        meas_id = measurement.get('Identifier')
        meas_t = measurement.find('.//'+ns_uri + 'RealTime')
        meas_t_live = measurement.find('.//'+ns_uri + 'LiveTime')
        print('Measurement ID:', meas_id) #this doesn't exist, just a placeholder
        print('  Real Time:', meas_t.text if meas_t is not None else 'N/A') 
        print('  Live Time:', meas_t_live.text if meas_t_live is not None else 'N/A')

        spectra = measurement.findall(ns_uri + 'Spectrum')
        for spectrum in spectra:
            spec_type = spectrum.get('Type')
            channel_data_elem = spectrum.find(ns_uri + 'ChannelData')
            if channel_data_elem is not None:
                compression_type = channel_data_elem.get('Compression')
                data_text = channel_data_elem.text.strip()
                data_values = list(map(int, data_text.split()))
                try:
                    if compression_type == 'CountedZeroes':
                        print("Detected Zero Compression -- decompressing")
                        counts = decompress_counted_zeros(data_values)
                    else:
                        counts = data_values
                except ValueError as e:
                    print(f"Error decompressing data: {e}")
                    continue  # Skip this spectrum if there's an error
                print('  Spectrum Type:', spec_type)

                channels = np.array(range(len(counts)))
    
                energy_calibration = spectrum.find('.//'+ns_uri + 'Calibration')
                p0=0
                p1=1
                if energy_calibration is not None:
                    coefficients_elem = energy_calibration.find('.//'+ns_uri + 'Coefficients')
                    if coefficients_elem is not None:
                        coeffs_text = coefficients_elem.text.strip()
                        coeffs = [float(c) for c in coeffs_text.split()]
                        print('  Calib coefficients:',coeffs)
                        p1=coeffs[1]
                        p0=coeffs[0]
                    else:
                        print('No Coefficients found in EnergyCalibration.')
                        coeffs = None
                else:
                    print('No EnergyCalibration found in Spectrum.')
                    coeffs = None    

                p1=p1*1.0193 #temp correction for wrong calibration
                energy = p0+p1*channels
                
                spectrum_data = {
                    'measurement_id': meas_id,
                    'spectrum_type': spec_type,
                    'channels': np.array(channels),
                    'counts': np.array(counts),
                    'energy': energy,
                    'real_time': re.search(r"\d+", meas_t.text).group() if meas_t is not None else 'N/A',
                    'live_time': re.search(r"\d+",meas_t_live.text).group() if meas_t_live is not None else 'N/A'
                }
                print()
                return spectrum_data

            else:
                print('No ChannelData found in Spectrum.')

#if __name__ == "__main__":
#    energy,counts=parse_n42_file('file.n42')


# In[ ]:

'''
data=parse_n42_file('137Cs.n42') #modify the filename accordingly


# In[ ]:


counts=data['counts']
energy=data['energy']
data['live_time']


# In[ ]:


#plot the 137-Cs line
plt.figure(figsize=(10, 6))
plt.step(energy, counts, where='mid') 
plt.xlabel('Energy [keV]',fontsize=18)
plt.ylabel('counts',fontsize=18)
ax=plt.gca()
plt.text(0.95,0.95,'Live time: '+data['live_time']+' s',transform=ax.transAxes, fontsize=18,verticalalignment='top', horizontalalignment='right')
plt.xlim(655,670)
#plt.ylim(0,500)
plt.grid(True,linestyle=':', linewidth='0.5', color='black')
plt.savefig('137Cs.png')


# In[ ]:


#plot the whole spectrum
plt.figure(figsize=(10, 6))
plt.step(energy, counts, where='mid') 
plt.xlabel('Energy [keV]',fontsize=18)
plt.ylabel('counts',fontsize=18)
plt.xlim(0,3000)
plt.yscale('log')
plt.grid(True,linestyle=':', linewidth='0.5', color='black')
ax = plt.gca()
plt.text(0.95,0.95,'Live time: '+data['live_time']+'s',transform=ax.transAxes, fontsize=18,verticalalignment='top', horizontalalignment='right')
plt.savefig('broad.png',transparent=False)


# In[ ]:
'''



