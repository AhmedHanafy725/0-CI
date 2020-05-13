<template>
  <div
    class="kt-aside kt-aside--fixed kt-grid__item kt-grid kt-grid--desktop kt-grid--hor-desktop"
    id="kt_aside"
  >
    <Aside-Sec />

    <!-- begin:: Aside Menu -->
    <Aside-Menu />
    <!-- end:: Aside Menu -->
  </div>

  <!-- end:: Aside -->
</template>

<script>
import Aside from "./Aside";
import AsideMenu from "./AsideMenu";
export default {
  name: "Sidebar",
  components: {
    "Aside-Sec": Aside,
    "Aside-Menu": AsideMenu
  }
};
</script>
