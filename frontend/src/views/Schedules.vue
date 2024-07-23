<template>
  <!-- begin:: Content -->
  <div>
    <Loading v-if="loading" />
    <div class="kt-portlet kt-portlet--mobile">
      <div class="kt-portlet__head kt-portlet__head--lg">
        <div class="kt-portlet__head-label">
          <span class="kt-portlet__head-icon">
            <i class="kt-font-brand flaticon2-line-chart"></i>
          </span>
          <h3 class="kt-portlet__head-title">{{ name }}</h3>
        </div>
        <div class="kt-header__topbar pr-0">
          <button
            type="button"
            class="btn btn-primary btn-sm text-white"
            :disabled="disabled"
            @click="restart()"
          >
            <i class="flaticon2-reload"></i> Restart build
          </button>
          <button
            type="button"
            class="kt-demo-icon mb-0"
            data-toggle="modal"
            :data-target="'#kt_modal_' + model"
            @click="runConfig()"
          >
            <i class="flaticon2-settings"></i>
          </button>
        </div>
      </div>
      <div class="kt-portlet__body">
        <v-card>
          <v-card-title>
            <!-- title -->
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>

            <v-text-field v-model="search" append-icon="mdi-magnify" label="Search"></v-text-field>
          </v-card-title>
          <v-data-table :headers="headers" :items="schedules" :search="search">
            <template v-slot:item.id="{ item }">
              <router-link
                :to="'/schedules/' + name + '/' + item.id"
              >{{schedules.length - schedules.map(function(x) {return x.id; }).indexOf(item.id)}}</router-link>
            </template>

            <template v-slot:item.status="{ item }">
              <v-chip :color="getStatus(item.status)" dark>{{ item.status }}</v-chip>
            </template>

            <template v-slot:item.timestamp="{ item }">
              <span>{{ time2TimeAgo(item.timestamp) }}</span>
            </template>
          </v-data-table>
        </v-card>
      </div>
    </div>

    <!-- :class="{'disabled': item.status == 'pending'}" -->
    <!--begin::Modal-->
    <div
      class="modal fade"
      id="kt_modal_4"
      tabindex="-1"
      role="dialog"
      aria-labelledby="exampleModalLabel"
      aria-hidden="true"
      v-if="newKeyModel"
    >
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="exampleModalLabel">Environment Variables</h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <!--begin::Form-->
            <span
              class="kt-spinner my-5 kt-spinner--v2 kt-spinner--lg kt-spinner--dark"
              v-if="formLoading"
            ></span>
            <!-- <div class="row" v-if="VarsValidate">
              <div class="offset-md-1 col">
                <div class="kt-section">
                  <div class="kt-section__info">{{ msg }}</div>
                </div>
              </div>
            </div>-->
            <form class="kt-form kt-form--label-right" @submit.prevent="addKey()">
              <div class="kt-portlet__body">
                <div class="form-group" v-if="keys">
                  <div class="row" v-for="(value, key, index) in keys" :key="index">
                    <div class="col align-self-center text-right">{{ index + 1}}.</div>
                    <div class="col-md-5">
                      <input class="form-control" type="text" :value="key" disabled />
                    </div>
                    <div class="col-md-5">
                      <input class="form-control" type="password" :value="value" disabled />
                    </div>
                    <div class="col align-self-center">
                      <i class="flaticon2-delete kt-font-error" @click="deleteKey(key, value)"></i>
                    </div>
                  </div>

                  <div class="row" v-if="fireInput">
                    <div class="offset-md-1 col-md-5">
                      <input
                        class="form-control"
                        type="text"
                        placeholder="Key"
                        v-model="newKey"
                        required
                      />
                    </div>
                    <div class="col-md-5">
                      <input
                        class="form-control"
                        type="text"
                        placeholder="Value"
                        v-model="newValue"
                        required
                      />
                    </div>
                  </div>

                  <div class="row">
                    <div class="offset-md-1 px-2">
                      <span class="kt-link" @click="fireInput = true, VarsValidate = false">
                        <i class="flaticon2-plus"></i>
                        Add new key
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="kt-portlet__foot text-right" v-if="fireInput">
                <div class="kt-form__actions">
                  <div class="row">
                    <div class="col">
                      <button type="submit" class="btn btn-success">Add</button>
                      <button type="reset" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                    </div>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>

    <!--end::Modal-->
  </div>

  <!-- end:: Content -->
</template>

<script>
import Loading from "../components/Loading";
import EventService from "../services/EventService";

export default {
  name: "ProjectDetails",
  props: ["name"],
  components: {
    Loading: Loading
  },
  data() {
    return {
      search: "",
      model: "",
      headers: [
        { text: "#ID", value: "id" },
        { text: "Status", value: "status" },
        { text: "Time", value: "timestamp" }
      ],
      schedules: null,
      loading: true,
      newKey: "",
      newValue: "",
      newKeyModel: true,
      disabled: false,
      fireInput: false,
      keys: null,
      formLoading: true,
      VarsValidate: false,
      msg: "No Variables Existed"
    };
  },
  methods: {
    clear() {
      this.schedules = [];
    },
    getDetails() {
      EventService.getSchedulesDetails(this.name)
        .then(response => {
          this.loading = false;
          this.schedules = response.data;
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    getStatus(status) {
      if (status == "error") return "kt-bg-error";
      else if (status == "failure") return "kt-bg-failure";
      else if (status == "success") return "kt-bg-success";
      else return "orange";
    },
    time2TimeAgo(ts) {
      var d = new Date();
      var nowTs = Math.floor(d.getTime() / 1000);
      var seconds = nowTs - ts;

      // more that two days
      if (seconds > 2 * 24 * 3600) {
        return "a few days ago";
      }
      // a day
      if (seconds > 24 * 3600) {
        return "yesterday";
      }

      if (seconds > 3600) {
        return "a few hours ago";
      }
      if (seconds > 1800) {
        return "Half an hour ago";
      }
      if (seconds > 60) {
        return Math.floor(seconds / 60) + " minutes ago";
      }
      if (seconds < 60) {
        return "Now";
      }
    },
    reset() {
      this.newKey = "";
      this.newValue = "";
    },
    restart() {
      if (this.$store.state.user !== null) {
        EventService.rebuildJob(this.name)
          .then(response => {
            if (response) {
              this.loading = false;
              this.disabled = true;
            }
          })
          .catch(error => {
            if (error.response.status == 401) {
              toastr.error("Please contact Adminstrator");
            } else {
              console.log("Error! Could not reach the API. " + error);
            }
          });
      } else {
        toastr.error("Please Login First!");
      }
    },
    runConfig() {
      if (
        this.$store.state.permission == "admin" ||
        this.$store.state.permission == "user"
      ) {
        this.fireInput = false;
        this.model = 4;
        EventService.runConfig(this.name)
          .then(response => {
            if (response) {
              this.formLoading = false;
              this.keys = response.data;
              // if (Object.keys(response.data).length === 0)
              if (response.data.length == undefined) {
                this.VarsValidate = true;
              }
            }
            if (this.keys == null) {
              this.VarsValidate = true;
            }
          })
          .catch(error => {
            console.log("Error! Could not reach the API. " + error);
          });
      } else if (this.$store.state.permission === "") {
        toastr.error("Please contact Adminstrator");
      } else {
        toastr.error("Please Login First!");
      }
    },
    addKey() {
      EventService.addKey(this.name, this.newKey, this.newValue)
        .then(response => {
          this.runConfig();
          this.fireInput = false;
          this.VarsValidate = false;
          this.reset();
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    deleteKey(key, value) {
      EventService.deleteKey(this.name, key, value)
        .then(response => {
          this.runConfig();
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    }
  },
  computed: {
    formatOrg() {
      return this.name.split(" ").join("%20");
    }
  },
  created() {
    this.getDetails();
  },
  mounted() {
    this.$options.sockets.onmessage = msg => {
      var data = JSON.parse(msg.data);

      let updated = this.schedules.find((o, i) => {
        if (o.id == data.id) {
          this.schedules[i].id = data.id;
          this.schedules[i].status = data.status;
          this.schedules[i].timestamp = data.timestamp;
          return true;
        }
      });
      if (updated == undefined) {
        this.schedules.unshift(data);
      }
    };
  },
  watch: {
    "$route.params": {
      handler(newValue) {
        this.clear();
        this.loading = true;
        const { name } = newValue;
        this.getDetails();
      },
      immediate: true
    }
  }
};
</script>

<style scoped>
.kt-spinner {
  margin: auto;
  display: table;
}

.kt-link,
.flaticon2-delete {
  cursor: pointer;
}
</style>
