package org;

import java.util.ArrayList;

public class Bank {
    String name;
    List<Person> user;

    public Bank(String name) {
        this.name = name;
        this.user = new ArrayList<>();
    }
}