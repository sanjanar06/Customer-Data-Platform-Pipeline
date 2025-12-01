package com.cdp.utils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

/**
 * Unit tests for IdentityNormalization utility class.
 * Verifies email and phone number rules
 */
public class IdentityNormalizationTest {

    @ParameterizedTest(name = "Testing email given {0} -> Expected {1}")
    @CsvSource(value = {
        "user+tag@example.com, user@example.com",           // Plus addressing removal
        "u.s.e.r@gmail.com, user@gmail.com",                // Gmail dots removal
        "Test.123+promo@googlemail.com, test123@googlemail.com", // Mixed normalization
        "test, test",                                        // Non-email string (graceful handling)
        ", "                                                 // Null input
    }, nullValues = {"", " "})
    void testNormalizeEmail(String input, String expected) {
        assertEquals(expected, IdentityNormalizer.normalizeEmail(input));
    }

    @ParameterizedTest(name = "Testing phone given {0} -> Expected {1}")
    @CsvSource({
        "123-456-7890, 1234567890",                         // Basic hyphens removal
        "+1 (555) 867-5309, 15558675309",                   // International format
        "'', ''"                                             // Empty string
    })
    void testNormalizePhone(String input, String expected) {
        assertEquals(expected, IdentityNormalizer.normalizePhone(input));
    }
    
}
