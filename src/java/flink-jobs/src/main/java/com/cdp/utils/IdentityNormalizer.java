package com.cdp.utils;

public class IdentityNormalizer {


    /**
     * Normalizes an email address by converting it to lowercase, removing dots from Gmail addresses,
     * and removing the part after '+' in the local part.
     *
     * @param email raw email string
     * @return normalized email string
     */
    public static String normalizeEmail(String email) {
        if (email == null) {
            return null;
        }
        String lowerCaseEmail = email.toLowerCase();

        int atIndex = lowerCaseEmail.indexOf('@');

        if (atIndex == -1) {
            return lowerCaseEmail; // Invalid email, return as is
        }

        String localPart = lowerCaseEmail.substring(0, atIndex);
        String domainPart = lowerCaseEmail.substring(atIndex + 1);

        // Remove plus addressing
        int plusIndex = localPart.indexOf('+');
        if (plusIndex != -1) {
            localPart = localPart.substring(0, plusIndex);
        }

        if (domainPart.equals("gmail.com") || domainPart.equals("googlemail.com")) {
            // Remove dots for Gmail addresses
            localPart = localPart.replace(".", "");
        }

        return localPart + "@" + domainPart;
    }

    public static String normalizePhone(String phoneNumber) {
        if (phoneNumber == null) {
            return null;
        }
        // Remove all non-digit characters
        return phoneNumber.replaceAll("[^0-9]", "");
    }

}
