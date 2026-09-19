// Nemean VR Helmet Internal Mounts (OpenSCAD CAD Source)
// Custom mounting frame for Raspberry Pi 5 & HUD Lens Bracket

$fn = 50;

// Base Pi 5 Mount Dimensions
pi_length = 85;
pi_width = 56;

module pi5_mount_plate() {
    difference() {
        cube([pi_length + 6, pi_width + 6, 8], center = true);
        cube([pi_length, pi_width, 10], center = true);
    }
}

// Internal lens bracket structure
pi5_mount_plate();
