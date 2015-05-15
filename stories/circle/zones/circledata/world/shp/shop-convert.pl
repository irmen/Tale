#!/usr/bin/perl -w

# This quick and dirty perl script was written to convert v3 shop files from
# using hard-coded numbers to using keywords.  The keywords are stored in
# the @item_types array found immediately after these comments.  Ensure that
# the order and contents of this array match the item types in your source
# code (defines found in structs.h, keywords in constant.c).
#
# Please note that this is not a supported script and is merely provided in
# an attempt to ease your life if you choose to use keywords rather than
# hard-coded values in the same fashion.
#
# ** IMPORTANT ** Back up your shop files before using this script, and verify
# the changes before booting up your mud.  This may make your mud unbootable
# if you do not verify the changes.
#
# ** IMPORTANT ** This only works on v3 shops (ie, ones that conform to the
# v3 format, and begin with the line 'CircleMUD v3.0 Shop File~'.  This will
# destroy v2 shop files.
#
# Usage:    shop-convert.pl [old shop file] > [new shop file]
# Example:  shop-convert.pl 1.shp > 1.shp.new
#

my @item_types = (
  "UNDEFINED",
  "LIGHT",
  "SCROLL",
  "WAND",
  "STAFF",
  "WEAPON",
  "FIRE WEAPON",
  "MISSILE",
  "TREASURE",
  "ARMOR",
  "POTION",
  "WORN",
  "OTHER",
  "TRASH",
  "TRAP",
  "CONTAINER",
  "NOTE",
  "LIQ CONTAINER",
  "KEY",
  "FOOD",
  "MONEY",
  "PEN",
  "BOAT",
  "FOUNTAIN",
);

my $state  = 0;
my $vthree = 0;
while (<>) {
  chomp;
  $vthree = 1 if (/^CircleMUD v3.0 Shop File~/);
  die "Use only on v3 format shop files.\n" unless ($vthree);
  if (/^#/) {
    $state = 1;
  } elsif ($state == 1) {
    $state++ if ($_ eq '-1');
  } elsif ($state == 2 || $state == 3) {
    $state++;
  } elsif ($state == 4) {
    if ($_ eq '-1') {
      $state++;
    } else {
      $_ = $item_types[$_];  # add 'lc' before '$item' to lower case.
    }
  }
  print "$_\n";
}

