package com.cdp.utils;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

public class JsonParser {
    
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();
    
    public static ObjectMapper getMapper() {
        return OBJECT_MAPPER;
    }
    
    public static JsonNode parse(String jsonString) throws Exception {
        return OBJECT_MAPPER.readTree(jsonString);
    }
    
    public static JsonNode safeParse(String jsonString) {
        try {
            return parse(jsonString);
        } catch (Exception e) {
            System.err.println("Failed to parse JSON: " + e.getMessage());
            return null;
        }
    }
    
    public static String toJson(Object object) throws Exception {
        return OBJECT_MAPPER.writeValueAsString(object);
    }
}
