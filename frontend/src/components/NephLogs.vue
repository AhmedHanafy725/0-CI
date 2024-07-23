<template>
  <v-expansion-panel>
    <v-expansion-panel-header>
      <span class="kt-portlet__head-icon text-left">
        <i class="kt-font-brand"></i>
        {{ title }}
      </span>
    </v-expansion-panel-header>
    <v-expansion-panel-content
      id="console"
      class="v-card v-card--flat v-sheet v-sheet--tile theme--dark"
    >
      <pre>
        <transition name="fade">
          <code v-html="html"></code>
        </transition>
      </pre>
    </v-expansion-panel-content>
  </v-expansion-panel>
</template>

<script>
import AnsiUp from "ansi_up";

export default {
  name: "NephLogs",
  props: ["nephID", "id"],
  data() {
    return {
      ansi: undefined,
      content: ""
    };
  },
  methods: {
    fetchLogs() {
      if (process.env.NODE_ENV === "development") {
        this.socket = new WebSocket(
          "ws://" +
            window.location.hostname +
            `/websocket/neph_logs/${this.nephID}`
        );
      } else {
        this.socket = new WebSocket(
          "wss://" +
            window.location.hostname +
            `/websocket/neph_logs/${this.nephID}`
        );
      }
      this.socket.onopen = () => {
        console.log("connected");
        this.socket.onmessage = ({ data }) => {
          this.content = data;
        };
      };
    }
  },
  computed: {
    html() {
      // Ensures we have some semblance of lines
      return this.ansi.ansi_to_html(this.content);
    },
    title() {
      return this.nephID
        .substring(this.nephID.indexOf(":") + 1)
        .replace("%20", " ")
        .replace(`${this.id}:`, "");
    }
  },
  beforeMount() {
    this.ansi = new AnsiUp();
  },
  watch: {
    livelogs(newValue) {
      this.content += newValue;
    }
  },
  updated() {
    var el = document.getElementById("console");
    el.scrollTop = el.scrollHeight;
  },
  created() {
    this.fetchLogs();
  }
};
</script>

<style scoped>
.v-card {
  max-height: 500px;
  font-family: monospace;
  overflow-y: auto;
}
code {
  box-shadow: none;
}

.kt-portlet .kt-portlet__body {
  overflow: hidden;
}

.kt-bg-success {
  font-weight: bold;
}

.v-application code {
  background-color: transparent;
  color: #fff;
  transition: all ease-in-out;
}

.fade-enter-active {
  transition: all ease-in-out;
}
.fade-leave-active {
  transition: all ease-in-out;
}
</style>
