package com.cdp.models;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import com.fasterxml.jackson.databind.JsonNode;

public class CustomerEvent {
    
    private String eventType;
    private long timestamp;
    private Map<String, String> identities;
    private Map<String, Object> properties;
    private JsonNode rawEvent;
    
    public CustomerEvent(JsonNode eventNode) {
        this.rawEvent = eventNode;
        this.identities = new HashMap<>();
        this.properties = new HashMap<>();
        
        if (eventNode.has("event_type")) {
            this.eventType = eventNode.get("event_type").asText();
        } else {
            this.eventType = "unknown";
        }
        
        if (eventNode.has("timestamp")) {
            this.timestamp = eventNode.get("timestamp").asLong();
        } else {
            this.timestamp = System.currentTimeMillis() / 1000;
        }
        
        if (eventNode.has("identities") && eventNode.get("identities").isObject()) {
            JsonNode identitiesNode = eventNode.get("identities");
            identitiesNode.fields().forEachRemaining(entry -> {
                this.identities.put(entry.getKey(), entry.getValue().asText());
            });
        }
        
        if (eventNode.has("properties") && eventNode.get("properties").isObject()) {
            JsonNode propertiesNode = eventNode.get("properties");
            propertiesNode.fields().forEachRemaining(entry -> {
                JsonNode value = entry.getValue();
                if (value.isTextual()) {
                    this.properties.put(entry.getKey(), value.asText());
                } else if (value.isNumber()) {
                    this.properties.put(entry.getKey(), value.asDouble());
                } else if (value.isBoolean()) {
                    this.properties.put(entry.getKey(), value.asBoolean());
                } else {
                    this.properties.put(entry.getKey(), value.toString());
                }
            });
        }
    }
    
    public List<Map<String, String>> getIdentitiesAsList() {
        List<Map<String, String>> identitiesList = new ArrayList<>();
        
        for (Map.Entry<String, String> entry : identities.entrySet()) {
            Map<String, String> identity = new HashMap<>();
            identity.put("type", entry.getKey());
            identity.put("value", entry.getValue());
            identitiesList.add(identity);
        }
        
        return identitiesList;
    }
    
    
    public String getEventType() {
        return eventType;
    }
    
    public long getTimestamp() {
        return timestamp;
    }
    
    public Map<String, String> getIdentities() {
        return identities;
    }
    
    public Map<String, Object> getProperties() {
        return properties;
    }
    
    public JsonNode getRawEvent() {
        return rawEvent;
    }
    
    public boolean hasIdentities() {
        return !identities.isEmpty();
    }
    
    @Override
    public String toString() {
        return String.format("CustomerEvent{eventType='%s', timestamp=%d, identities=%d, properties=%d}",
                eventType, timestamp, identities.size(), properties.size());
    }
}
