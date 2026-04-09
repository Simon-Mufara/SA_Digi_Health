rule Lab_Safety_Violation
{
    strings:
        $person = "person"
        $bottle = "bottle"

    condition:
        $person and $bottle
}
