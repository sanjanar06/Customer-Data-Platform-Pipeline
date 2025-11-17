package com.cdp.processors;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;

import com.cdp.models.CustomerEvent;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

public class ProfileStitcherTest {
    
    private final ObjectMapper mapper = new ObjectMapper();
    
    @Test
    void testCustomerEventParsing() throws Exception {
        // Arrange
        String eventJson = "{"
                + "\"event_type\": \"purchase\","
                + "\"timestamp\": 1699876543,"
                + "\"identities\": {"
                + "  \"email\": \"test@example.com\","
                + "  \"deviceID\": \"device_123\""
                + "},"
                + "\"properties\": {"
                + "  \"product\": \"Laptop\","
                + "  \"price\": 999.99"
                + "}"
                + "}";
        
        JsonNode eventNode = mapper.readTree(eventJson);
        
        // Act
        CustomerEvent event = new CustomerEvent(eventNode);
        
        // Assert
        assertEquals("purchase", event.getEventType());
        assertEquals(1699876543L, event.getTimestamp());
        assertTrue(event.hasIdentities());
        assertEquals(2, event.getIdentities().size());
        assertEquals("test@example.com", event.getIdentities().get("email"));
        assertEquals("device_123", event.getIdentities().get("deviceID"));
    }
    
    @Test
    void testIdentitiesAsListConversion() throws Exception {
        // Arrange
        String eventJson = "{"
                + "\"event_type\": \"page_view\","
                + "\"identities\": {"
                + "  \"email\": \"user@test.com\","
                + "  \"userID\": \"user_456\""
                + "}"
                + "}";
        
        JsonNode eventNode = mapper.readTree(eventJson);
        CustomerEvent event = new CustomerEvent(eventNode);
        
        // Act
        List<Map<String, String>> identitiesList = event.getIdentitiesAsList();
        
        // Assert
        assertEquals(2, identitiesList.size());
        
        boolean hasEmail = identitiesList.stream()
                .anyMatch(id -> "email".equals(id.get("type")) && "user@test.com".equals(id.get("value")));
        boolean hasUserId = identitiesList.stream()
                .anyMatch(id -> "userID".equals(id.get("type")) && "user_456".equals(id.get("value")));
        
        assertTrue(hasEmail, "Should have email identity");
        assertTrue(hasUserId, "Should have userID identity");
    }
    
    @Test
    void testEventWithNoIdentities() throws Exception {
        // Arrange
        String eventJson = "{\"event_type\": \"system_event\"}";
        JsonNode eventNode = mapper.readTree(eventJson);
        
        // Act
        CustomerEvent event = new CustomerEvent(eventNode);
        
        // Assert
        assertFalse(event.hasIdentities());
        assertTrue(event.getIdentitiesAsList().isEmpty());
    }
    
    @Test
    void testEventProperties() throws Exception {
        // Arrange
        String eventJson = "{"
                + "\"event_type\": \"purchase\","
                + "\"properties\": {"
                + "  \"product\": \"Phone\","
                + "  \"price\": 599.99,"
                + "  \"quantity\": 2"
                + "}"
                + "}";
        
        JsonNode eventNode = mapper.readTree(eventJson);
        
        // Act
        CustomerEvent event = new CustomerEvent(eventNode);
        Map<String, Object> properties = event.getProperties();
        
        // Assert
        assertEquals(3, properties.size());
        assertEquals("Phone", properties.get("product"));
        assertEquals(599.99, properties.get("price"));
        assertEquals(2.0, properties.get("quantity"));
    }
}

