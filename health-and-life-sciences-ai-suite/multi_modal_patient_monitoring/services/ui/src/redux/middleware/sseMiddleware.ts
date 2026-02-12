import type { Middleware } from '@reduxjs/toolkit';
import { addEvent } from '../slices/eventsSlice';
import { updateWorkloadData, setAggregatorStatus } from '../slices/servicesSlice';

export const sseMiddleware: Middleware = (store) => {
  let eventSource: EventSource | null = null;

  return (next) => (action) => {
    if (typeof action !== 'object' || action === null || !('type' in action)) {
      return next(action);
    }

    // Handle SSE connect
    if (action.type === 'sse/connect') {
      const url = (action as any).payload?.url;
      
      if (!url) {
        console.error('[SSE] ❌ No URL provided');
        return next(action);
      }

      if (eventSource) {
        console.warn('[SSE] ⚠️ Already connected, closing existing connection');
        eventSource.close();
        eventSource = null;
      }

      console.log('[SSE] 🔌 Connecting to:', url);
      store.dispatch(setAggregatorStatus('connecting'));

      eventSource = new EventSource(url);

      eventSource.onopen = () => {
        console.log('[SSE] ✅ Connection established');
        store.dispatch(setAggregatorStatus('connected'));
      };

      eventSource.onmessage = (event) => {
        try {
          const rawData = JSON.parse(event.data);
          console.log('[SSE] 📨 Raw message:', rawData);

          const workloadType = rawData.workload_type || rawData.workload;
          const eventType = rawData.event_type || 'data';
          const payload = rawData.payload || rawData;
          const timestamp = rawData.timestamp || Date.now();

          // Parse workload-specific data
          let parsedData: any = {};

          if (workloadType === 'rppg') {
            // rPPG sends: HEART_RATE, RESP_RATE, SpO2, waveform
            const metricType = payload.metric;
            
            if (metricType === 'HEART_RATE') {
              parsedData.HR = payload.value ?? payload.HR;
            } else if (metricType === 'RESP_RATE') {
              parsedData.RR = payload.value ?? payload.RR;
            } else if (metricType === 'SPO2') {
              parsedData.SpO2 = payload.value ?? payload.SpO2;
            }
            
            // Extract waveform if present
            if (payload.waveform && Array.isArray(payload.waveform)) {
              parsedData.waveform = payload.waveform;
              parsedData.waveformFrequency = payload.fs || payload.waveform_frequency_hz;
            }
            
            console.log('[SSE] ✓ Parsed rPPG:', {
              metric: metricType,
              vitals: { HR: parsedData.HR, RR: parsedData.RR, SpO2: parsedData.SpO2 },
              waveformLength: parsedData.waveform?.length
            });
          
          } else if (workloadType === 'ai-ecg') {
            console.log('[SSE] 🔬 AI-ECG raw payload:', JSON.stringify(payload, null, 2));
            
            // AI-ECG sends: inference object + waveform
            parsedData.prediction = payload.inference ?? 'Unknown';

            // ✅ Filename
            parsedData.filename = payload.file ?? 'Unknown';

            // ✅ Waveform
            if (Array.isArray(payload.waveform)) {
              parsedData.waveform = payload.waveform;
            }

            // ✅ Waveform frequency (very useful for ECG chart scaling)
            if (payload.waveform_frequency_hz) {
              parsedData.waveformFrequency = payload.waveform_frequency_hz;
            }
            
            console.log('[SSE] ✅ Final AI-ECG parsedData:', {
              prediction: parsedData.prediction,
              filename: parsedData.filename,
              waveformLength: parsedData.waveform?.length,
              allKeys: Object.keys(parsedData)
            });
            
          } else if (workloadType === 'mdpnp') {
            console.log('[SSE] 🏥 MDPNP raw payload:', JSON.stringify(payload, null, 2));
            
            const eventType = rawData.event_type;
            const deviceType = rawData.device_type || payload.device_type;
            
            if (eventType === 'numeric') {
              const metric = payload.metric;
              
              // ECG_Simulator metrics
              if (metric === 'MDC_ECG_HEART_RATE') {
                parsedData.HR = payload.value;
                console.log('[SSE] ✓ MDPNP ECG HR:', payload.value);
              } 
              else if (metric === 'MDC_TTHOR_RESP_RATE') {
                parsedData.RR = payload.value;
                console.log('[SSE] ✓ MDPNP Respiration Rate:', payload.value);
              }
              
              // CO2_Simulator metrics
              else if (metric === 'MDC_AWAY_CO2_ET') {
                parsedData.CO2_ET = payload.value;
                console.log('[SSE] ✓ MDPNP CO2_ET:', payload.value);
              }
              else if (metric === 'MDC_CO2_RESP_RATE') {
                parsedData.CO2_RR = payload.value;
                console.log('[SSE] ✓ MDPNP CO2 Respiration Rate:', payload.value);
              }
              
              // IBP_Simulator metrics
              else if (metric === 'MDC_PRESS_BLD_ART_ABP_SYS') {
                parsedData.BP_SYS = payload.value;
                console.log('[SSE] ✓ MDPNP BP Systolic:', payload.value);
              } 
              else if (metric === 'MDC_PRESS_BLD_ART_ABP_DIA') {
                parsedData.BP_DIA = payload.value;
                console.log('[SSE] ✓ MDPNP BP Diastolic:', payload.value);
              }
            } 
            else if (eventType === 'waveform') {
              if (payload.waveform && Array.isArray(payload.waveform)) {
                const metric = payload.metric;
                
                if (metric === 'MDC_ECG_LEAD_II') {
                  parsedData.waveform = payload.waveform;
                  parsedData.waveformType = 'ECG';
                  parsedData.waveformFrequency = payload.waveform_frequency_hz;
                  console.log('[SSE] ✓ MDPNP ECG waveform:', payload.waveform.length, 'samples @', payload.waveform_frequency_hz, 'Hz');
                } 
                else if (metric === 'MDC_AWAY_CO2') {
                  parsedData.waveform = payload.waveform;
                  parsedData.waveformType = 'CO2';
                  parsedData.waveformFrequency = payload.waveform_frequency_hz;
                  console.log('[SSE] ✓ MDPNP CO2 waveform:', payload.waveform.length, 'samples @', payload.waveform_frequency_hz, 'Hz');
                } 
                else if (metric === 'MDC_PRESS_BLD') {
                  parsedData.waveform = payload.waveform;
                  parsedData.waveformType = 'BP';
                  parsedData.waveformFrequency = payload.waveform_frequency_hz;
                  console.log('[SSE] ✓ MDPNP BP waveform:', payload.waveform.length, 'samples @', payload.waveform_frequency_hz, 'Hz');
                }
              }
            }
            
            console.log('[SSE] ✓ Parsed MDPNP:', {
              vitals: { 
                HR: parsedData.HR, 
                RR: parsedData.RR,
                CO2_ET: parsedData.CO2_ET, 
                CO2_RR: parsedData.CO2_RR,
                BP_SYS: parsedData.BP_SYS,
                BP_DIA: parsedData.BP_DIA 
              },
              waveformType: parsedData.waveformType,
              waveformLength: parsedData.waveform?.length
            });
            
          } else if (workloadType === '3d-pose') {
            let allPeopleJoints: any[] = [];
            
            console.log('[SSE] Raw 3D Pose payload:', payload);
            
            if (payload.people && Array.isArray(payload.people) && payload.people.length > 0) {
              // ✅ Extract joints from ALL people, not just the first one
              allPeopleJoints = payload.people.map((person: any) => {
                return {
                  person_id: person.person_id,
                  joints_3d: person.joints_3d || [],
                  confidence: person.confidence || [],
                };
              });
              
              console.log('[SSE] ✓ Extracted joints from all people:', {
                totalPeople: allPeopleJoints.length,
                jointsPerPerson: allPeopleJoints.map(p => p.joints_3d.length),
              });
            }
            
            parsedData = {
              activity: payload.activity || 'Unknown',
              people: allPeopleJoints,  // ✅ Send all people
              num_persons: payload.people?.length || 0,
              frame_number: payload.frame_number || 0,
            };

            // ✅ Always include frame data immediately (no throttling)
            if (payload.frame_base64) {
              parsedData.frameData = `data:image/jpeg;base64,${payload.frame_base64}`;
              console.log(`[SSE] 🎬 Frame received for ${workloadType}`);
            }

            console.log('[SSE] ✓ Dispatching to Redux:', parsedData);
            
          } else {
            console.warn(`[SSE] ⚠️ Unknown workload type: ${workloadType}`);
          }

          // Dispatch to Redux
          store.dispatch(updateWorkloadData({
            workloadId: workloadType,
            data: parsedData,
            timestamp: timestamp
          }));

          // Also add to events log
          store.dispatch(addEvent({
            workload: workloadType,
            data: parsedData,
            timestamp: timestamp
          }));

        } catch (error) {
          console.error('[SSE] ❌ Parse error:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('[SSE] ❌ Connection error:', error);
        store.dispatch(setAggregatorStatus('error'));
        
        if (eventSource) {
          eventSource.close();
          eventSource = null;
        }

        // Auto-reconnect after 5 seconds
        setTimeout(() => {
          const state = store.getState();
          if (state.app?.isProcessing) {
            console.log('[SSE] 🔄 Attempting reconnect...');
            store.dispatch({ type: 'sse/connect', payload: { url } });
          }
        }, 5000);
      };
    }

    // Handle SSE disconnect
    if (action.type === 'sse/disconnect') {
      console.log('[SSE] 🔌 Disconnecting...');
      
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
      
      store.dispatch(setAggregatorStatus('stopped'));
    }

    return next(action);
  };
};